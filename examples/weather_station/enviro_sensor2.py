from blezero import Device, Sensor, IRRADIANCE, TEMPERATURE, PRESSURE, HUMIDITY
from picographics import PicoGraphics, DISPLAY_PICOVISION, PEN_DV_RGB555 as PEN
import network
import urequests
import ntptime
import time
import machine
import gc
import uasyncio as asyncio
import pngdec

try:
    from secrets import WIFI_SSID, WIFI_PASSWORD
    credentials_available = True
except ImportError:
    print("Create secrets.py with your WiFi credentials to get time from NTP")
    credentials_available = False
    
# General settings:
# set this to True if you don't want your mirror to display your WiFi password
REDACT_WIFI = True

# Adjust the clock to show the correct timezone
UTC_OFFSET = 1.0

# how often to poll the APIs for data, in minutes
UPDATE_INTERVAL = 15

# Weather settings:
# Weather from OpenMeteo - find out more at https://open-meteo.com/

# Set your latitude/longitude here (find yours by right clicking in Google Maps!)
LAT = 53.38609085276884
LNG = -1.4239983439328177
TIMEZONE = "auto"  # determines time zone from lat/long
WEATHER_URL = "http://api.open-meteo.com/v1/forecast?latitude=" + str(LAT) + "&longitude=" + str(LNG) + "&current_weather=true&timezone=" + TIMEZONE


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

# Create a new PNG decoder for our PicoGraphics
png = pngdec.PNG(graphics)

# create the rtc object
rtc = machine.RTC()

# some other variables for keeping track of stuff
timer = 0
second = 0
last_second = 0
temperature = None
wifi_problem = False


# Connect to wifi, synchronize the RTC time from NTP and download data from our APIs
def get_data():
    global wifi_problem
    if not credentials_available:
        return

    # Start connection
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm=0xa11140)  # Turn WiFi power saving off for some slow APs
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    # Wait for connect success or failure
    max_wait = 100
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for WiFi connection...')
        time.sleep(0.2)

    if wlan.isconnected():
        print("WiFi connected")
        wifi_problem = False

        try:
            print("Setting time from NTP")
            ntptime.settime()
            print(f"Time set (UTC): {rtc.datetime()}")
        except Exception as e:
            print(e)

        get_weather_data()


    else:
        print(f"Wifi not connected - status code: {wlan.status()}")
        wifi_problem = True


def get_weather_data():
    global temperature, windspeed, winddirection, weathercode, date, now
    try:
        print("Requesting weather data")
        r = urequests.get(WEATHER_URL)
        # open the json data
        j = r.json()
        print("Weather data obtained:")
        print(j)
        # parse relevant data from JSON
        current = j["current_weather"]
        temperature = current["temperature"]
        windspeed = current["windspeed"]
        winddirection = calculate_bearing(current["winddirection"])
        weathercode = current["weathercode"]
        date, now = current["time"].split("T")
        r.close()
    except Exception as e:
        print(e)


def calculate_bearing(d):
    # calculates a compass direction from the wind direction in degrees
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    ix = round(d / (360. / len(dirs)))
    return dirs[ix % len(dirs)]


def display_forecast(x, y):
    
    graphics.set_pen(GREEN)
    graphics.rectangle(x, y, WIDTH//2, HEIGHT)
    
    # lets have some weather
    graphics.set_pen(WHITE)
    graphics.text("FORECAST", x, y, scale=2)
    if temperature is not None:
        # Choose an appropriate icon based on the weather code
        # Weather codes from https://open-meteo.com/en/docs
        # Weather icons from https://icons8.com/
        if weathercode in [71, 73, 75, 77, 85, 86]:  # codes for snow
            png.open_file("/icons/snow.png")
        elif weathercode in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:  # codes for rain
            png.open_file("/icons/rain.png")
        elif weathercode in [1, 2, 3, 45, 48]:  # codes for cloud
            png.open_file("/icons/cloud.png")
        elif weathercode in [0]:  # codes for sun
            png.open_file("/icons/sun.png")
        elif weathercode in [95, 96, 99]:  # codes for storm
            png.open_file("/icons/storm.png")
        png.decode(x + 20, y + 20)
        # draw the weather text
        graphics.set_pen(WHITE)
        graphics.text("Temperature", x + 20, y + 120, scale=2)
        graphics.text(f"{temperature}°C", x + 30, y + 150, scale=5)
        graphics.text("Wind speed", x + 20, y + 180, scale=2)
        graphics.text(f"{windspeed}kmph {winddirection}", x + 30, y + 200, scale=5)
        graphics.text(f"Last OpenMeteo data: {now}, {date}", x + 20, y + 300, scale=1)
    else:
        graphics.text("Weather data not available.", x, y + 50, scale=1)
        

def display_indoor(x, y, light, temp, pressure, hum):
    graphics.set_pen(TEAL)
    graphics.rectangle(x, y, WIDTH//2, HEIGHT)
    draw_house(x + 30, y + 30)
    graphics.set_pen(WHITE)
    graphics.text("INDOOR", x, y, scale=2)
    
    graphics.text("Temperature", x + 20, y + 50, scale=1)
    graphics.text(f"{temp}°C", x + 30, y + 60, scale=5)
    graphics.text("Humidity", x + 20, y + 150, scale=1)
    graphics.text(f"{hum}%", x + 30, y + 160, scale=5)
    graphics.text("Pressure", x + 20, y + 250, scale=1)
    graphics.text(f"{pressure}Pa", x + 30, y + 260, scale=5)
    
def display_outdoor(x, y, light, temp, pressure, hum):
    graphics.set_pen(YELLOW)
    graphics.rectangle(x, y, WIDTH//2, HEIGHT)
    
    graphics.set_pen(WHITE)
    graphics.text("INDOOR", x, y, scale=2)
    
    graphics.text("Temperature", x + 20, y + 50, scale=1)
    graphics.text(f"{temp}°C", x + 30, y + 60, scale=5)
    graphics.text("Humidity", x + 20, y + 150, scale=1)
    graphics.text(f"{hum}%", x + 30, y + 160, scale=5)
    graphics.text("Pressure", x + 20, y + 250, scale=1)
    graphics.text(f"{pressure}Pa", x + 30, y + 260, scale=5)
    


def draw_bluetooth(x,y):
    graphics.line(x, y + 5, x + 10, y + 15)
    graphics.line(x, y + 15, x + 10, y + 5)
    graphics.line(x + 10, y + 5, x + 5, y)
    graphics.line(x + 10, y + 15, x + 5, y + 20)
    graphics.line(x + 5, y, x + 5, y + 20)

def draw_house(x,y):
    graphics.set_pen(YELLOW)
    graphics.line(x, y + 10, x + 15, y)
    graphics.line(x + 15, y, x + 30, y + 10)
    graphics.line(x + 5, y + 10, x + 5, y + 30)
    graphics.line(x + 25, y + 10, x + 25, y + 30)
    graphics.line(x + 5, y + 30, x + 25, y + 30)
    
def draw_header():
    year, month, day, h, min, _, wday, _ = time.localtime()
    
    # sety day of the week
    weekday = "Monday"
    if wday == 1:  weekday = "Tuesday"
    elif wday == 2: weekday = "Wednesday"
    elif wday == 3: weekday = "Thursday"
    elif wday == 4: weekday = "Friday"
    elif wday == 5: weekday = "Saturday"
    elif wday == 6: weekday = "Sunday"
    
    minute = str(min)
    if min < 10: minute = "0" + minute
    
    hour = str(h)
    if h < 10: hour = "0" + hour
    
    graphics.text(f"{weekday} {day}/{month}/{year}  {hour}:{minute}", 10, 0, scale = 2)
    draw_bluetooth(300,0)
    
    graphics.line(0, 30, WIDTH, 30)
   
devices = (
    Device(
        'enviro-indoor',
        Sensor("Light", 160, IRRADIANCE, drange=(0, 150)),
        Sensor("Temp", 160, TEMPERATURE, drange=(20, 40)),
        Sensor("Pressure", 160, PRESSURE, drange=(1000, 1100)),
        Sensor("Humidity", 160, HUMIDITY, drange=(0, 100))
    ),
    Device(
        'enviro-weather',
        Sensor("Light", 160, IRRADIANCE, drange=(0, 150)),
        Sensor("Temp", 160, TEMPERATURE, drange=(20, 40)),
        Sensor("Pressure", 160, PRESSURE, drange=(1000, 1100)),
        Sensor("Humidity", 160, HUMIDITY, drange=(0, 100))
    )
)

async def main():
    while True:
        get_data()
        
#         await devices[0].update()
        for device in devices:
            await device.update()

        
        await refresh_display()
        await asyncio.sleep_ms(1000)



async def refresh_display():
    print("Display draw...")
    graphics.set_pen(BLACK)
    graphics.clear()
    graphics.set_pen(WHITE)
    draw_header()
    
    
    
    indoor_light_reading = devices[0].sensors[0].get_current_reading()
    indoor_temp_reading = devices[0].sensors[1].get_current_reading()
    indoor_pressure_reading = devices[0].sensors[2].get_current_reading()
    indoor_humidity_reading = devices[0].sensors[3].get_current_reading()
    
    weather_light_reading = devices[1].sensors[0].get_current_reading()
    weather_temp_reading = devices[1].sensors[1].get_current_reading()
    weather_pressure_reading = devices[1].sensors[2].get_current_reading()
    weather_humidity_reading = devices[1].sensors[3].get_current_reading()
    
    display_outdoor(0, 30, weather_light_reading, weather_temp_reading, weather_pressure_reading, weather_humidity_reading)
#     display_forecast(0, 30)
    display_indoor(WIDTH - WIDTH//2, 30, indoor_light_reading, indoor_temp_reading, indoor_pressure_reading, indoor_humidity_reading)
    print("Display update...")
    graphics.update()



asyncio.run(main())
    
