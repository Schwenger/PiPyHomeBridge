"Allows for altering requests based on time"

import math
from typing import Tuple
from datetime import datetime
from colour import Color
from light import LightState

midnight        = ( 0, Color("DarkGreen"), "midnight")
night           = ( 2, Color("Red"), "night")
early_morning   = ( 4, Color("Orange"), "early morning")
morning         = ( 7, Color("Yellow"), "morning")
day             = (11, Color("White"), "day")
afternoon       = (15, Color("Yellow"), "afternoon")
evening         = (18, Color("Orange"), "evening")
zones = [midnight, night, early_morning, morning, day, afternoon, evening]

def recommended() -> LightState:
    "Returns the recommended light state for the current time of day."
    time = _time_as_float()
    return _recommended(time)

def _recommended(time: float) -> LightState:
    color = _recommended_color(time)
    brightness = _recommended_brightness(time)
    temp = _recommended_temp(time)
    return LightState(True, brightness, temp, color)

def _time_as_float() -> float:
    now = datetime.now()
    return now.hour + (now.minute/60)

def _recommended_brightness(time: float) -> float:
    return 1 - (abs(12 - time) / 12)

def _recommended_temp(time: float) -> float:
    return _recommended_brightness(time)

def _recommended_color(time: float) -> Color:
    for start, end in zip(zones, zones[1:]):
        if start[0] <= time < end[0]:
            return _color_in_zone(time, start, end)
    end_color = zones[0][1]
    return _color_in_zone(time, zones[-1], (24, end_color, "irrelevant"))

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

# def _offset_color_temp(col: Color, offset: int) -> Color:
#     col.hue += offset * 0.2
#     return col