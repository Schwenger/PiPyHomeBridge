"Allows for altering requests based on time"

import math
from typing import Tuple
from datetime import datetime
from colour import Color
from light import LightState

zones = [
    ( 0, Color("DarkGreen"), "midnight"),
    ( 2, Color("Red"),       "night"),
    ( 4, Color("Orange"),    "early morning"),
    ( 7, Color("Yellow"),    "morning"),
    (11, Color("White"),     "day"),
    (15, Color("Yellow"),    "afternoon"),
    (18, Color("Orange"),    "evening"),
]

def recommended() -> LightState:
    "Returns the recommended light state for the current time of day."
    current_time = datetime.now()
    time = _time_as_float(current_time)
    return _recommended(time)

def _time_as_float(time: datetime) -> float:
    return time.hour + (time.minute/60)

def _recommended(time: float) -> LightState:
    color = _recommended_color(time)
    brightness = _recommended_brightness(time)
    temp = _recommended_temp(time)
    return LightState(True, brightness, temp, color)

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
