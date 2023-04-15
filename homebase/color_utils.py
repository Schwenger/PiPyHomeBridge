"A collection of useful color-related functions."

from math import isclose
from colormath.color_objects import HSVColor as Color

def equal(this: Color, that: Color) -> bool:
    "Compares two colors."
    hue = isclose(this.hsv_h, that.hsv_h)
    sat = isclose(this.hsv_s, that.hsv_s)
    val = isclose(this.hsv_v, that.hsv_v)
    return hue and sat and val

def white() -> Color:
    "Returns a white color."
    return Color(0, 0, 1)
