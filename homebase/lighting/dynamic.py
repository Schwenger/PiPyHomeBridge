"Allows for altering requests based on time"

import math
from datetime import datetime
from typing import Tuple

from colormath.color_objects import HSVColor
from lighting.state import State

colors = {
    "DarkGreen": HSVColor(hsv_h=0.33, hsv_s=1, hsv_v=0.2),
    "Red":       HSVColor(hsv_h=0.00, hsv_s=1, hsv_v=1.0),
    "Orange":    HSVColor(hsv_h=0.10, hsv_s=1, hsv_v=1.0),
    "Yellow":    HSVColor(hsv_h=0.17, hsv_s=1, hsv_v=1.0),
    "White":     HSVColor(hsv_h=0.00, hsv_s=0, hsv_v=1.0),
}

zones = [
    ( 0, colors["DarkGreen"], "midnight"),
    ( 2, colors["Red"],       "night"),
    ( 4, colors["Orange"],    "early morning"),
    ( 7, colors["Yellow"],    "morning"),
    (11, colors["White"],     "day"),
    (15, colors["Yellow"],    "afternoon"),
    (18, colors["Orange"],    "evening"),
]


def recommended() -> State:
    "Returns the recommended light state for the current time of day."
    current_time = datetime.now()
    time = _time_as_float(current_time)
    return _recommended(time)


def _time_as_float(time: datetime) -> float:
    return time.hour + (time.minute / 60)


def _recommended(time: float) -> State:
    color = _recommended_color(time)
    brightness = _recommended_brightness(time)
    color.hsv_v = brightness
    return State(True, color)

def _recommended_brightness(time: float) -> float:
    return 1 - (abs(12 - time) / 12)

def _recommended_color(time: float) -> HSVColor:
    for start, end in zip(zones, zones[1:]):
        if start[0] <= time < end[0]:
            return _color_in_zone(time, start, end)
    end_color = zones[0][1]
    return _color_in_zone(time, zones[-1], (24, end_color, "irrelevant"))


def _color_in_zone(
    time: float,
    current_zone: Tuple[int, HSVColor, str],
    next_zone: Tuple[int, HSVColor, str]
) -> HSVColor:
    from colour import Color
    from colormath.color_objects import sRGBColor
    from colormath.color_conversions import convert_color
    (start, start_color, _) = current_zone
    (end, end_color, _) = next_zone
    resolution = (end - start) * 2  # 30 min steps
    start_rgb: sRGBColor = convert_color(start_color, sRGBColor)
    end_rgb: sRGBColor = convert_color(end_color, sRGBColor)
    range_start = Color(start_rgb.get_rgb_hex())
    range_end = Color(end_rgb.get_rgb_hex())
    colors = list(range_start.range_to(range_end, resolution))
    steps_in_zone = (math.floor(time) - start) * 2
    if time % 1 > 0.5:
        steps_in_zone += 1
    target = colors[steps_in_zone]
    target_rgb = sRGBColor(rgb_b=target.blue, rgb_g=target.green, rgb_r=target.red)
    return convert_color(target_rgb, HSVColor)
