"Everything regarding payloads"

from typing import Optional
import json
from colour import Color
from device import Vendor

__DEFAULT_TRANS = 2
DEFAULT_DIMMING_SPEED = 40


class Payload:
    "A class for creating payloads."

    def __init__(self):
        self.body = {}

    def state(self, toggled_on: Optional[bool]) -> 'Payload':
        "Sets the state or queries it if None."
        if toggled_on is None:
            target = ""
        elif toggled_on:
            target = "ON"
        else:
            target = "OFF"
        self.body["state"] = target
        return self

    def brightness(self, val: Optional[float]) -> 'Payload':
        "Sets the brightness to val or queries it if none"
        target = _Bright.scaled(val) if val is not None else ""
        self.body["brightness"] = target
        return self

    def white_temp(self, val: Optional[float], vendor: Vendor) -> 'Payload':
        "Sets the white temp to val or queries it if none"
        target = _WhiteTemp.scaled(val, vendor) if val is not None else ""
        self.body["color_temp"] = target
        return self

    def color(self, col: Optional[Color], _vendor: Vendor) -> 'Payload':
        "Sets the color to col or queries it if none"
        target = { "hex": col.get_hex_l() } if col is not None else ""
        self.body["color"] = target
        return self

    def with_transition(self, time: Optional[float] = None) -> 'Payload':
        "Adds a transition component to the payload."
        self.body["transition"] = time or __DEFAULT_TRANS
        return self

    def finalize(self) -> str:
        "Finalizes the payload in json format."
        return Payload.prep_for_sending(self.body)

    @staticmethod
    def cleanse(value):
        "Cleanses the value of swift-incompatible symbols."
        return value.replace("\"[", "[").replace("]\"", "]").replace("'", "\"")

    @staticmethod
    def __brightness_move(val: float) -> str:
        res = Payload()
        res.body["brightness_move"] = val
        return res.finalize()

    @staticmethod
    def start_dim(down: bool, speed: int = DEFAULT_DIMMING_SPEED) -> str:
        "Starts gradually reducing or increasing the brightness."
        factor = -1 if down else 1
        return Payload.__brightness_move(factor * speed)

    @staticmethod
    def stop_dim() -> str:
        "Stops gradually changing the brightness."
        return Payload.__brightness_move(0)

    @staticmethod
    def rename(old: str, new: str) -> str:
        "Returns a payload to rename a device."
        res = Payload()
        res.body["from"] = old
        res.body["to"]   = new
        return res.finalize()

    @staticmethod
    def __as_json(data: dict) -> str:
        return json.dumps(data)

    @staticmethod
    def prep_for_sending(data: dict) -> str:
        "Prepares a payload for sending."
        return Payload.cleanse(Payload.__as_json(data))

################################################
# READING
################################################


def read_brightness(val: str) -> float:
    "Returns the white temperature as scale based on the value retrieved from the device."
    return _Bright.from_device(int(val))


def read_state(val: str) -> bool:
    "Returns the white temperature as scale based on the value retrieved from the device."
    return val == "ON"


def read_white_temp(val: str, vendor: Vendor) -> float:
    "Returns the white temperature as scale based on the value retrieved from the device."
    return _WhiteTemp.read(int(val), vendor)


def read_color(x: float, y: float, Y: float) -> Color:
    "Returns the color temperature based on the value retrieved from the device."
     # pylint: disable=invalid-name
    # x/y to x/y/z
    z = 1.0 - x - y
    # x/y/z to X/Y/Z
    X = (Y / y) * x if y > 0 else 0
    Z = (Y / y) * z if y > 0 else 0
    # X/Y/Z to r/g/b
    r = X * 1.4628067 - Y * 0.1840623 - Z * 0.2743606
    g = -X * 0.5217933 + Y * 1.4472381 + Z * 0.0677227
    b = X * 0.0349342 - Y * 0.0968930 + Z * 1.2884099
    # Gamma-correction
    r = 12.92 * r if r <= 0.0031308 else (1.0 + 0.055) * pow(r, (1.0 / 2.4)) - 0.055
    g = 12.92 * g if g <= 0.0031308 else (1.0 + 0.055) * pow(g, (1.0 / 2.4)) - 0.055
    b = 12.92 * b if b <= 0.0031308 else (1.0 + 0.055) * pow(b, (1.0 / 2.4)) - 0.055
    return Color(rgb=(r, g, b))


class _Bright:
    "Deals with brightness values, translates relative brightnesses into absolute values."
    max: int = 254
    min: int = 0

    @staticmethod
    def scaled(scale: float) -> int:
        "Returns the absolute brightness for a scalar ∈ [0,1]."
        return int(_Bright.max * scale)

    @staticmethod
    def from_device(val: int) -> float:
        "Returns the scalar based on the value retrieved from the device."
        return float(val) / _Bright.max


class _WhiteTemp:
    "Deals with white color temperature"
    cfg = {
        Vendor.Ikea: {
            "min":  250,
            "max":  454,
            "diff": 454 - 250,
        },
        Vendor.Hue: {
            "min":  153,
            "max":  500,
            "diff": 500 - 153,
        }
    }

    @staticmethod
    def scaled(scale: float, vendor: Vendor) -> float:
        "Returns the absolute brightness for a scalar ∈ [0,1]."
        return _WhiteTemp.cfg[vendor]["diff"] * (1 - scale) + _WhiteTemp.cfg[vendor]["min"]

    @staticmethod
    def read(val: int, vendor: Vendor) -> float:
        "Returns the scalar based on the value retrieved from the device."
        upper = _WhiteTemp.cfg[vendor]["diff"]
        val = val - _WhiteTemp.cfg[vendor]["min"]
        return 1 - (float(val) / upper)
