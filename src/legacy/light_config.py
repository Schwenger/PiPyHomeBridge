"Allows for altering requests based on time"

import math
from typing import Tuple
from datetime import datetime
from colour import Color

class LightConfig():
    "A configuration of any light source."

    def __init__(self, brightness: float, white_temp: float, color_temp: Color):
        self._brightness: float = brightness
        self._white_temp: float = white_temp
        self._color_temp: Color = color_temp

    @property
    def brightness(self) -> float:
        "Returns the brightness."
        return self._brightness

    @property
    def white_temp(self) -> float:
        "Returns the white temperature."
        return self._white_temp

    @property
    def color(self) -> Color:
        "Returns the color."
        return self._color_temp

    @property
    def is_on(self) -> bool:
        "Is config on?"
        return self.brightness > 0

    @staticmethod
    def off() -> 'LightConfig':
        "Off config"
        return LightConfig(0, 0, Color("White"))

    def with_hue_offset(self, hue: int) -> 'LightConfig':
        "Reduces or increases brightness  and turns color (counter-)clockwise."
        self._color_temp = _offset_color_temp(self._color_temp, hue)
        return self

    def with_brightness(self, brightness: float) -> 'LightConfig':
        "Sets the brightness to the specified value"
        self._brightness = brightness
        self._white_temp = self.brightness
        return self

    def purge_color(self) -> 'LightConfig':
        "Returns an identical LightConfig just with a white color."
        self._color_temp = Color("White")
        return self

    def purge_dimming(self) -> 'LightConfig':
        "Returns an identical LightConfig just with a max brightness."
        self._brightness = 1
        self._white_temp = 1
        return self

    @staticmethod
    def recommended() -> 'LightConfig':
        "Returns the recommended light configuration for the current time of day."
        time = LightConfig._time_as_float()
        return _recommended(time)

    @staticmethod
    def _time_as_float() -> float:
        now = datetime.now()
        return now.hour + (now.minute/60)

midnight        = ( 0, Color("DarkGreen"), "midnight")
night           = ( 2, Color("Red"), "night")
early_morning   = ( 4, Color("Orange"), "early morning")
morning         = ( 7, Color("Yellow"), "morning")
day             = (11, Color("White"), "day")
afternoon       = (15, Color("Yellow"), "afternoon")
evening         = (18, Color("Orange"), "evening")
zones = [midnight, night, early_morning, morning, day, afternoon, evening]

def _offset_color_temp(val: Color, offset: int) -> Color:
    val.hue += offset * 0.2
    return val

def _recommended_brightness(time: float) -> float:
    return 1 - (abs(12 - time) / 12)

def _recommended_temp(time: float) -> float:
    return _recommended_brightness(time)

def _color_in_zone(
    time: float,
    current_zone: Tuple[int, Color, str],
    next_zone: Tuple[int, Color, str]
) -> Color:
    (start, start_color, _) = current_zone
    (end, end_color, _) = next_zone
    resolution = (end - start) * 2  # 30 min steps
    colors = list(start_color.range_to(end_color, resolution))
    steps_in_zone = (math.floor(time) - start) * 2
    if time % 1 > 0.5:
        steps_in_zone += 1
    return colors[steps_in_zone]

def _recommended_color(time: float) -> Color:
    for start, end in zip(zones, zones[1:]):
        if start[0] <= time < end[0]:
            return _color_in_zone(time, start, end)
    end_color = zones[0][1]
    return _color_in_zone(time, zones[-1], (24, end_color, "irrelevant"))

def _recommended(time: float) -> LightConfig:
    color = _recommended_color(time)
    brightness = _recommended_brightness(time)
    temp = _recommended_temp(time)
    return LightConfig(brightness, temp, color)
