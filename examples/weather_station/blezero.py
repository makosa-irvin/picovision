import struct
import aioble
import uasyncio as asyncio
import bluetooth
from micropython import const

"""
Handle connections to the Enviro Indoor and Weather sensors via BLE

"""
# org.bluetooth.service.environmental_sensing
ENVIRONMENTAL_SENSING = bluetooth.UUID(0x181A)

TEMPERATURE = const(0x2A6E)  # org.bluetooth.characteristic.temperature
PRESSURE = const(0x2A6D)
HUMIDITY = const(0x2A6F)
RAIN = const(0x2A78)
IRRADIANCE = const(0x2A77)   # It's not Lux, but it'll do for now

# Helpers to decode the temperature, light, pressure and humidity readings
def _decode_temperature(data):
    return struct.unpack("<h", data)[0] / 100.0

def _decode_light(data):
    # 0.1 W/m2
    return struct.unpack("<h", data)[0] / 10.0

def _decode_pressure(data):
    return struct.unpack("<h", data)[0] / 10.0

def _decode_humidity(data):
    # uint16t: % with a resolution of 0.01
    return struct.unpack("<h", data)[0] / 100.0


DECODERS = {
    TEMPERATURE: _decode_temperature,
    PRESSURE: _decode_pressure,
    HUMIDITY: _decode_humidity,
    IRRADIANCE: _decode_light,
}


class Sensor:
    def __init__(self, caption, samples, uuid, drange=None):
        self.caption = caption
        self.uuid = bluetooth.UUID(uuid)
        self._length = samples
        self.dlog = [None for _ in range(self._length)]
        self.dptr = 0
        self.decode = DECODERS[uuid]
        print(self.decode)
        self.lower = 0
        self.upper = 1
        self.autorange = drange is None
        if not self.autorange:
            self.lower, self.upper = drange
            
    @property
    def length(self):
        try:
            return self.dlog.index(None)
        except ValueError:
            return self._length

    async def update(self, characteristic):
        value = await characteristic.read()
        value = self.decode(value)

        if self.autorange:
            self.lower = min(self.dlog)
            self.lower = min(self.lower, value)
            self.upper = max(self.dlog)
            self.upper = min(self.upper, value)

        self.dlog[self.dptr] = value

        if self.dptr == self._length - 1:
            for i in range(1, self._length):
                self.dlog[i - 1] = self.dlog[i]
        else:
            self.dptr += 1
        
    def avg(self):
        """
        Calculate the minimum, maximum and average readings
        """
        if self.dptr == 0:
            return 0
        v = 0
        max_reading = 0
        min_reading = self.dlog[0]
        # Avoid using sum(self.dlog[:self.dptr]) since it allocates memory
        for i in range(self.dptr):
            if self.dlog[i] > max_reading:
                max_reading = self.dlog[i]
            elif self.dlog[i] < min_reading:
                min_reading = self.dlog[i]
            v += self.dlog[i]
        return (v / self.dptr), max_reading, min_reading

    def get_scaled(self, index, scale=1.0):
        value = self.dlog[index]
        if value is None:
            raise ValueError("Unpopulated reading")
        value = min(self.upper, value)
        value = max(self.lower, value)
        value -= self.lower
        value /= (self.upper - self.lower)
        value *= scale
        return value

    def draw_graph(self, graphics, x, y, w, h, bar_color, caption_color, bar_width=4, bar_margin=2):
        bar_spacing = bar_width + bar_margin
        graphics.set_pen(bar_color)

        end_reading = self.length
        start_reading = max(0, self.length - int(w / bar_spacing))
        bar_x = 0

        for i in range(start_reading, end_reading):
            reading = int(self.get_scaled(int(i), h))
            graphics.rectangle(x + bar_x, y + h - reading, bar_width, reading)
            bar_x += bar_spacing

        gavg, gmax, gmin = self.avg()
        graphics.set_pen(caption_color)
        graphics.text(f"{self.caption}", x , y, scale=2)
        graphics.text(f"avg: {gavg:.2f}", x, y + 16, scale=1)
        graphics.text(f"max: {gmax:.2f}", x, y + 32, scale=1)
        graphics.text(f"min: {gmin:.2f}", x, y + 48, scale=1)

    def get_current_reading(self):
        gavg, gmax, gmin = self.avg()
        current_val = self.dlog[self.dptr-1]

        if current_val is None:
            return "No reading yet"
        
        return current_val
class Device:
    def __init__(self, name, *args):
        self.uuid = ENVIRONMENTAL_SENSING
        self.name = name
        self.sensors = args
        self.device = None
        
    async def find(self):
        if self.device is None:
            async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
                async for result in scanner: 
                    # See if it matches our name and the environmental sensing service.
                    print(result)
                    if result.name() == self.name and self.uuid in result.services():
                        self.device = result.device
                        return self.device
        return self.device

    async def update(self):
        print(f"Updating {self.name}")
        device = await self.find()
        
        try:
            connection = await device.connect()
        except asyncio.TimeoutError:
            print("Timeout during connection")
            return
    
        print("Connected...")
        
        service = await connection.service(ENVIRONMENTAL_SENSING)
        if service is None:
            print("Could not find ENVIRONMENTAL_SENSING service")
            return

        async with connection:
            for sensor in self.sensors:
                try:
                    characteristic = await service.characteristic(sensor.uuid)
                    print(f"Update {sensor.caption} {sensor.uuid}")
                except asyncio.TimeoutError:
                    print("Timeout discovering services/characteristics")
                    continue

                await sensor.update(characteristic)
                await asyncio.sleep_ms(10)