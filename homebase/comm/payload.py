"Everything regarding payloads"

import json
from typing import Optional

from colour import Color
from enums import Vendor

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
        target = { "hex": col.get_hex_l().upper() } if col is not None else ""
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
    def __remove_redundancy(data: dict) -> dict:
        if "color" in data:
            del data["color_temp"]
        return data

    @staticmethod
    def prep_for_sending(data: dict) -> str:
        "Prepares a payload for sending."
        data = Payload.__remove_redundancy(data)
        as_str = Payload.__as_json(data)
        as_str = Payload.cleanse(as_str)
        return as_str

################################################
# READING
################################################

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
