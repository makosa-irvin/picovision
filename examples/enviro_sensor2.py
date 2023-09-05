import uasyncio as asyncio
import time
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


has_sprite = False  # set if the sprite file exists in the pico

try:
    # load the sprites
    # Given that the png image is 64 by 64 pixels it is split to 4 portions of 32 by 32 pixels
    # This is done by providing a 4 tuple as third argument as (x_offset, y_offset, portion_width, portion_height)
    for _ in range(2):
        graphics.load_sprite("bluetooth_icon.png", 1)
        graphics.update()

    has_sprite = True
except OSError as ioe:
    if ioe.errno not in (errno.ENOENT):
        raise
    has_sprite = False

def draw_temp_icon(x,y):
    
    graphics.circle(x,y,10)
    

# draws a sun icon
def draw_sun(x, y, r):
    circle_x = x + 3 + r
    circle_y = y + 3 + r
    graphics.circle(circle_x, circle_y, r)
    graphics.line(circle_x, y, circle_x, y + 2)
    graphics.line(x, circle_y, x + 2, circle_y)
    graphics.line(circle_x, (y + 5 + 2 * r), circle_x, (y + 5 + 2 * r) + 2)
    graphics.line((x + 5 + 2 * r), circle_y, (x + 5 + 2 * r) + 2, circle_y)
    graphics.line(
        circle_x + 1 + r, circle_y - 1 - r, circle_x + 3 + r, circle_y - 3 - r
    )
    graphics.line(
        circle_x + 1 + r, circle_y + 1 + r, circle_x + 3 + r, circle_y + 3 + r
    )
    graphics.line(
        circle_x - 1 - r, circle_y - 1 - r, circle_x - 3 - r, circle_y - 3 - r
    )
    graphics.line(
        circle_x - 1 - r, circle_y + 1 + r, circle_x - 3 - r, circle_y + 3 + r
    )
    

def draw_header(device_name):
    year, month, day, hour, minute, _, _, _ = time.localtime()
    
    graphics.text(f"{day}/{month}/{year}  {hour}:{minute}", 10, 0, scale = 2)
    graphics.display_sprite(1, 1, 200, 0)
    graphics.text(f"{device_name}", 250, 0, scale=2)
    
    graphics.line(0, 40, WIDTH, 40)
   
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
    graphics.set_pen(WHITE)
    draw_header("enviro-indoor")
    
    temp_reading = device.sensors[1].get_current_reading(graphics)
    graphics.text(f"{temp_reading}", 100, 100, scale=2)
    print("Display update...")
    graphics.update()



asyncio.run(main())
    
