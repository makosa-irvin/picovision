import uasyncio as asyncio
from blezero import Device, Sensor, IRRADIANCE, TEMPERATURE, PRESSURE, HUMIDITY
from picographics import PicoGraphics, PEN_RGB555 as PEN

"""
In this example weather data from the Enviro weather and indoor devices is displayed on a HDMI screen
A bar graph of each sensor on a given device is drawn and its respective data is frequently updated
Ensure that the blezero file is uploaded to the pico
Enviro weather(https://shop.pimoroni.com/products/enviro-weather-board-only)
Enviro Indoor(https://shop.pimoroni.com/products/enviro-indoor)

"""

graphics = PicoGraphics(width=640, height=480, pen_type=PEN)
WIDTH, HEIGHT = graphics.get_bounds()

# Pen colour constants
WHITE = graphics.create_pen(255, 255, 255)
BLACK = graphics.create_pen(0, 0, 0)
RED = graphics.create_pen(255, 0, 0)
GREEN = graphics.create_pen(0, 255, 0)
BLUE = graphics.create_pen(0, 0, 255)
YELLOW = graphics.create_pen(255, 255, 0)
TEAL = graphics.create_pen(0, 255, 255)
PURPLE = graphics.create_pen(255, 0, 255)

# display constants
RIGHT_MARGIN = 12
LEFT_MARGIN = 22
SENSOR_TOP_MARGIN = 2
DEVICE_TOP_MARGIN = 14 + SENSOR_TOP_MARGIN
GRAPH_MARGIN = 24

# Buffers
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

# Add the enviro devices
devices = (
    Device(
        "enviro-indoor",
        Sensor("Light", 160, IRRADIANCE, drange=None),
        Sensor("Temp", 160, TEMPERATURE, drange=(20, 40)),
        Sensor("Pressure", 160, PRESSURE, drange=(1000, 1100)),
        Sensor("Humidity", 160, HUMIDITY, drange=(0, 100)),
    ),
    Device(
        "enviro-weather",
        Sensor("Light", 160, IRRADIANCE, drange=None),
        Sensor("Temp", 160, TEMPERATURE, drange=(20, 40)),
        Sensor("Pressure", 160, PRESSURE, drange=(1000, 1100)),
        Sensor("Humidity", 160, HUMIDITY, drange=(0, 100)),
    ),
)


async def main():
    """First updates each each connected device and then refresh the display"""
    while True:
        for device in devices:
            await device.update()

        await refresh_display()
        await asyncio.sleep_ms(1000)


async def refresh_display():
    """Draws and updates the bar graphs for each sensor"""
    print("Display draw...")

    graphics.set_pen(BLACK)
    graphics.clear()
    W = int(WIDTH // 2)
    H = int(HEIGHT // 4)

    GW = W - GRAPH_MARGIN  # Graph width
    GH = H - GRAPH_MARGIN  # Graph height
    graphics.set_pen(WHITE)

    # draws graphs of each sensor in the devices
    text1_width = graphics.measure_text(f"{devices[0].name}", scale=2)
    graphics.text(f"{devices[0].name}", WIDTH // 2 - text1_width // 2, 0, scale=2)
    devices[0].sensors[0].draw_graph(
        graphics,               # display
        0 + LEFT_MARGIN,        # x position
        0 + DEVICE_TOP_MARGIN,  # y position
        GW,                     # graph width
        GH,                     # graph height
        BLUE,                   # bar colour
        WHITE                   # text colour
    )
    devices[0].sensors[1].draw_graph(graphics, W + RIGHT_MARGIN, 0 + DEVICE_TOP_MARGIN, GW, GH, RED, WHITE)
    devices[0].sensors[2].draw_graph(graphics, 0 + LEFT_MARGIN, H, GW, GH, GREEN, WHITE)
    devices[0].sensors[3].draw_graph(graphics, W + RIGHT_MARGIN, H, GW, GH, TEAL, WHITE)

    graphics.line(0, HEIGHT // 2, WIDTH, HEIGHT // 2)

    text2_width = graphics.measure_text(f"{devices[1].name}", scale=2)
    graphics.text(
        f"{devices[1].name}", WIDTH // 2 - text2_width // 2, HEIGHT // 2 + 2, scale=2
    )
    devices[1].sensors[0].draw_graph(graphics, 0 + LEFT_MARGIN, (H * 2) + 0 + DEVICE_TOP_MARGIN, GW, GH, BLUE, WHITE)
    devices[1].sensors[1].draw_graph(graphics, W + RIGHT_MARGIN, (H * 2) + 0 + DEVICE_TOP_MARGIN, GW, GH, RED, WHITE)
    devices[1].sensors[2].draw_graph(graphics, 0 + LEFT_MARGIN, (H * 2) + H, GW, GH, GREEN, WHITE)
    devices[1].sensors[3].draw_graph(graphics, W + RIGHT_MARGIN, (H * 2) + H, GW, GH, TEAL, WHITE)

    print("Display update...")
    graphics.update()


asyncio.run(main())
