"A module containing the state of a light."

import math
from typing import List
from colour import Color

class State:
    "Represents the state of a light."
    def __init__(
        self,
        toggled_on: bool = False,
        brightness: float = 0,
        white_temp: float = 0,
        color: Color = Color("White")
    ):
        self.toggled_on: bool = toggled_on
        self.brightness: float = brightness
        self.white_temp: float = white_temp
        self.color: Color = color

    @staticmethod
    def max() -> 'State':
        return State(
            toggled_on=True,
            brightness=1,
            white_temp=1,
            color=Color("White")
        )

    def with_color(self, color: Color):
        "Reduces or increases brightness  and turns color (counter-)clockwise."
        self.color = color

    def with_brightness(self, brightness: float):
        "Sets the brightness to the specified value"
        self.brightness = brightness
        self.white_temp = self.brightness

    def purge_color(self):
        "Returns an identical LightConfig just with a white color."
        self.color = Color("White")

    def purge_dimming(self):
        "Returns an identical LightConfig just with a max brightness."
        self.brightness = 1
        self.white_temp = 1

    @staticmethod
    def average(states: List['State']) -> 'State':
        "Returns a light state that roughly resembles the average light state of the given ones."
        ons = 0
        brightness = 0.0
        white_temp = 0.0
        red = 0.0
        green = 0.0
        blue = 0.0
        for state in states:
            ons += int(state.toggled_on)
            brightness += state.brightness
            white_temp += state.white_temp
            red += state.color.get_red()**2
            green += state.color.get_green()**2
            blue += state.color.get_blue()**2
        # pylint: disable=invalid-name
        n = len(states)
        red = math.sqrt(red / n)
        green = math.sqrt(green / n)
        blue = math.sqrt(blue / n)
        return State(
            toggled_on=ons / n >= 0.5,
            brightness=brightness / n,
            white_temp=white_temp / n,
            color=Color(rgb=(red, green, blue))
        )

