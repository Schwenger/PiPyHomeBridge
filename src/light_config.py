"Allows for altering requests based on time"

import math
from typing import Tuple
from datetime import datetime
from colour import Color

class LightConfig():
    "A configuration of any light source."

    def __init__(self, brightness: float, white_temp: float, color_temp: Color):
        self.brightness = brightness
        self.white_temp = white_temp
        self.color_temp = color_temp
        self.is_on = brightness > 0

    def offset_by(self, brightness: int, hue: int) -> 'LightConfig':
        "Reduces or increases brightness  and turns color (counter-)clockwise."
        self.brightness = _offset_brightness(self.brightness, brightness)
        self.white_temp = _offset_white_temp(self.white_temp, brightness)
        self.color_temp = _offset_color_temp(self.color_temp, hue)
        return self

    def purge_color(self) -> 'LightConfig':
        "Returns an identical LightConfig just with a white color."
        self.color_temp = Color("White")
        return self

    def purge_dimming(self) -> 'LightConfig':
        "Returns an identical LightConfig just with a max brightness."
        self.brightness = 1
        self.white_temp = 1
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

LightConfig.ON =  LightConfig(1, 1, Color("White"))

midnight        = ( 0, Color("DarkGreen"), "midnight")
night           = ( 2, Color("Red"), "night")
early_morning   = ( 4, Color("Orange"), "early morning")
morning         = ( 7, Color("Yellow"), "morning")
day             = (11, Color("White"), "day")
afternoon       = (15, Color("Yellow"), "afternoon")
evening         = (18, Color("Orange"), "evening")
zones = [midnight, night, early_morning, morning, day, afternoon, evening]

def _push_within_bound(val, lower, upper):
    return min(max(val, lower), upper)

def _offset_brightness(val: int, offset: int) -> int:
    with_offset = val + offset * 0.2
    within_bounds = _push_within_bound(with_offset, lower=0, upper=1)
    return within_bounds

def _offset_white_temp(val: int, offset: int) -> int:
    return _offset_brightness(val, offset)

def _offset_color_temp(val: Color, offset: int) -> int:
    val.hue += offset * 0.2
    return val

def _recommended_brightness(time: float) -> Color:
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
