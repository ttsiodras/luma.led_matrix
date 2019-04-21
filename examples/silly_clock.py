#!/usr/bin/env python
import os
import time
from datetime import datetime

from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.legacy import text, show_message
from luma.core.legacy.font import proportional, CP437_FONT, TINY_FONT


def minute_change(device):
    '''When we reach a minute change, animate it.'''
    hours = datetime.now().strftime('%H')
    minutes = datetime.now().strftime('%M')

    def helper(current_y):
        with canvas(device) as draw:
            text(draw, (0, 1), hours, fill="white", font=proportional(CP437_FONT))
            text(draw, (15, 1), ":", fill="white", font=proportional(TINY_FONT))
            text(draw, (17, current_y), minutes, fill="white", font=proportional(CP437_FONT))
        time.sleep(0.1)
    for current_y in range(1, 9):
        helper(current_y)
    minutes = datetime.now().strftime('%M')
    for current_y in range(9, 1, -1):
        helper(current_y)


def animation(device, from_y, to_y):
    '''Animate the whole thing, moving it into/out of the abyss.'''
    hourstime = datetime.now().strftime('%H')
    mintime = datetime.now().strftime('%M')
    current_y = from_y
    while current_y != to_y:
        with canvas(device) as draw:
            text(draw, (0, current_y), hourstime, fill="white", font=proportional(CP437_FONT))
            text(draw, (15, current_y), ":", fill="white", font=proportional(TINY_FONT))
            text(draw, (17, current_y), mintime, fill="white", font=proportional(CP437_FONT))
        time.sleep(0.1)
        current_y += 1 if to_y > from_y else -1


def main():
    # Check whether we configured the environment with an OpenWeatherMap key.
    if 'OPENWEATHERMAP_APIKEY' in os.environ:
        openWeatherMapKey = os.environ['OPENWEATHERMAP_APIKEY']
        bOpenWeatherMap = True
    else:
        print("No OpenWeather key found (env var OPENWEATHERMAP_APIKEY). Disabling temperature reports...")
        bOpenWeatherMap = False

    # Setup for Banggood version of 4 x 8x8 LED Matrix (https://bit.ly/2Gywazb)
    serial = spi(port=0, device=0, gpio=noop())
    device = max7219(serial, cascaded=4, block_orientation=-90, blocks_arranged_in_reverse_order=True)
    device.contrast(2)

    # The time ascends from the abyss...
    animation(device, 8, 1)

    toggle = False  # Toggle the second indicator every second

    def getTemperature():
        if not bOpenWeatherMap:
            return "N/A"
        cmd = "curl -s 'https://api.openweathermap.org/data/2.5/weather?q=Leiden,NL&appid="
        cmd += openWeatherMapKey + "&units=metric' | json_pp | grep temp..:"
        try:
            newTemperature = os.popen('bash -c "' + cmd + '"').readlines()[0]
            return newTemperature.split()[-1].replace(',', '') + 'C'
        except Exception:
            return temperature
    temperature = getTemperature()
    while True:
        toggle = not toggle
        n = datetime.now()
        if bOpenWeatherMap and n.minute % 5 == 0:
            temperature = getTemperature()
        if n.second == 59:
            # When we change minutes, animate the minute change
            minute_change(device)
        elif n.second == 30:
            # Half-way through each minute, display the complete date/time,
            # animating the time display into and out of the abyss.
            full_msg = time.ctime()
            animation(device, 1, 8)
            show_message(device, full_msg, fill="white", font=proportional(CP437_FONT))
            animation(device, 8, 1)
        elif bOpenWeatherMap and n.second % 15 == 0:
            # Show temperature (if an OpenWeatherMap key was configured in the env)
            animation(device, 1, 8)
            show_message(device, "Temperature: " + temperature, fill="white", font=proportional(CP437_FONT))
            animation(device, 8, 1)
        else:
            # Most of the time, do this update. Now, I'd optimize this if I had to ;
            # but even my Raspberry PI2 can do this at 4% of a single one... of the 4 cores!
            hours = datetime.now().strftime('%H')
            minutes = datetime.now().strftime('%M')
            with canvas(device) as draw:
                text(draw, (0, 1), hours, fill="white", font=proportional(CP437_FONT))
                text(draw, (15, 1), ":" if toggle else " ", fill="white", font=proportional(TINY_FONT))
                text(draw, (17, 1), minutes, fill="white", font=proportional(CP437_FONT))
            # Do this twice each second (to blink the hour/minute indicator - i.e. ':')
            time.sleep(0.5)


if __name__ == "__main__":
    main()
