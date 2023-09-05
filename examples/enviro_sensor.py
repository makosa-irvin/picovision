import uasyncio as asyncio
from blezero import Device, Sensor, IRRADIANCE, TEMPERATURE, PRESSURE, HUMIDITY

from picographics import PicoGraphics, DISPLAY_PICOVISION, PEN_DV_RGB555 as PEN


graphics = PicoGraphics(DISPLAY_PICOVISION, width=640, height=480, pen_type=PEN)
WIDTH, HEIGHT = graphics.get_bounds()

WHITE = graphics.create_pen(255, 255, 255)
BLACK = graphics.create_pen(0, 0, 0)
RED = graphics.create_pen(255, 0, 0)
GREEN = graphics.create_pen(0, 255, 0)
BLUE = graphics.create_pen(0, 0, 255)
YELLOW = graphics.create_pen(255, 255, 0)
TEAL = graphics.create_pen(0, 255, 255)
PURPLE = graphics.create_pen(255, 0, 255)


graphics.set_pen(TEAL)
graphics.clear()
graphics.set_pen(RED)
graphics.text("BUFFER 1", 0, 0, 4)
graphics.update()

graphics.set_pen(TEAL)
graphics.clear()
graphics.set_pen(RED)
graphics.text("BUFFER 2", 0, 0, 4)
graphics.update()

print("Cleared...")

device = (
    Device(
        'enviro-indoor',
        Sensor("Light", 160, IRRADIANCE, drange=(0, 150)),
        Sensor("Temp", 160, TEMPERATURE, drange=(20, 40)),
        Sensor("Pressure", 160, PRESSURE, drange=(1000, 1100)),
        Sensor("Humidity", 160, HUMIDITY, drange=(0, 100))
    )
)

async def main():
    while True:
       
        await device.update()

        await refresh_display()
        await asyncio.sleep_ms(1000)


async def refresh_display():
    print("Display draw...")

    graphics.set_pen(BLACK)
    graphics.clear()
    W = int(WIDTH // 2)
    H = int(HEIGHT // 2)

    GW = W - 4
    GH = H - 4
    
    device.sensors[0].draw_graph(graphics, 0+2, 0+2, GW, GH, BLUE, WHITE)
    device.sensors[1].draw_graph(graphics, W+2, 0+2, GW, GH, RED, WHITE)
    device.sensors[2].draw_graph(graphics, 0+2, H+2, GW, GH, GREEN, WHITE)
    device.sensors[3].draw_graph(graphics, W+2, H+2, GW, GH, TEAL, WHITE)

    print("Display update...")
    graphics.update()



asyncio.run(main())