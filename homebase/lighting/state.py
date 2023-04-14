"A module containing the state of a light."

from colormath.color_conversions import convert_color
from colormath.color_objects import xyYColor, HSVColor
from comm import payload


class State:
    "Represents the state of a light."
    def __init__(
        self,
        color: HSVColor = HSVColor(0, 0, 1)
    ):
        self._color: HSVColor = color

    @property
    def toggled_on(self) -> bool:
        "Whether the state claims to be on or off."
        return self._color.hsv_v > 0.0

    @toggled_on.setter
    def toggled_on(self, is_on: bool):
        "Sets the state ot be toggled on or off."
        if is_on:
            self._color.hsv_v = max(self._color.hsv_v, 0.05)
        else:
            self._color.hsv_v = 0.0

    @property
    def color(self) -> HSVColor:
        "Color of the state."
        return self._color

    @color.setter
    def color(self, new: HSVColor):
        "Sets the color of the state."
        self._color = new

    def __str__(self) -> str:
        onoff = "On" if self.toggled_on else "Off"
        return f"<{onoff} with color {self._color}>"

    @staticmethod
    def max() -> 'State':
        "Returns a maximal state, full light emission."
        return State(
            color=HSVColor(0, 0, 1)
        )

    @staticmethod
    def read_light_state(desc: dict) -> 'State':
        "Returns the state of the light."
        state = State()
        bright = 0
        if "brightness" in desc:
            bright = State.__read_brightness(desc["brightness"])
        if "color_mode" in desc:
            if desc["color_mode"] == "xy":
                val_x = desc["color"]["x"]
                val_y = desc["color"]["y"]
                xyy = xyYColor(xyy_x=val_x, xyy_y=val_y, xyy_Y=bright)
                state.color = convert_color(xyy, HSVColor)
        if State.__read_state(desc["state"]):
            bright = max(0.05, bright)
        else:
            bright = 0
        return state

    @staticmethod
    def __read_brightness(val: str) -> float:
        "Returns the white temperature as scale based on the value retrieved from the device."
        return payload.Bright.from_device(int(val))

    @staticmethod
    def __read_state(val: str) -> bool:
        "Returns the white temperature as scale based on the value retrieved from the device."
        return val == "ON"
