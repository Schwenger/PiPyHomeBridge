"Allows for altering requests based on time"

import math
from enum import Enum
from typing import Tuple
from datetime import datetime
from colour import Color

class Brightness(Enum):
    "The level of dimming for any quasi-light"
    OFF = -3
    SUB_TWO_THIRDS = -2
    SUB_ONE_THIRD = -1
    NEUTRAL = 0
    ADD_ONE_THIRD = 1
    ADD_TWO_THIRDS = 2
    SPOTLIGHT = 3

    def apply_to(self, brightness: float) -> float:
        "Reduces or increases the given brightness based on the dimming level."
        factor = 1/3 * self.value
        leeway = brightness if self.value < 0 else (1-brightness)
        return brightness + leeway * factor

    def inc(self) -> 'Brightness':
        "Increases brightness."
        return self.with_bias(+1)

    def dec(self) -> 'Brightness':
        "Decreases brightness."
        return self.with_bias(-1)

    def with_bias(self, bias: int) -> 'Brightness':
        "In- or decreases brightness by the specified bias."
        return Brightness(max(-3, min(3, self.value + bias)))


class LightConfig():
    "A configuration of any light source."

    def __init__(self, brightness: float, white_temp: float, color_temp: Color):
        self.brightness: float = brightness
        self.white_temp: float = white_temp
        self.color_temp: Color = color_temp
        self.is_on: bool = brightness > 0

    @staticmethod
    def off() -> 'LightConfig':
        "Off config"
        return LightConfig(0, 0, Color("White"))

    def with_hue_offset(self, hue: int) -> 'LightConfig':
        "Reduces or increases brightness  and turns color (counter-)clockwise."
        self.color_temp = _offset_color_temp(self.color_temp, hue)
        return self

    def with_dim_level(self, dim_level: Brightness) -> 'LightConfig':
        "Sets the brightness to the specified value"
        self.brightness = dim_level.apply_to(self.brightness)
        self.white_temp = self.brightness
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
