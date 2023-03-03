"Everything regarding payloads"

from typing import Optional
import json
from colour import Color
from device import Vendor

DEFAULT_TRANS = 2
DEFAULT_DIMMING_SPEED = 40

################################################
##### SENDING
################################################
def state(value: Optional[bool]) -> str:
    "Creates a payload for a state change."
    match value:
        case None:  val = ""
        case True:  val = "ON"
        case False: val = "OFF"
    return _json(_with_transition({"state" : val}))

def brightness(value: Optional[float]) -> str:
    "Returns a payload to set or retrieve the brightness."
    if value is None:
        return _json(_with_transition({"brightness": ""}))
    return _json(_with_transition({"brightness": _Bright.scaled(value)}))

def white_temp(value: Optional[float], vendor: Vendor) -> str:
    "Returns a payload to set or retrieve the color temp."
    if value is None:
        return _json(_with_transition({"color_temp": ""}))
    payload = {"color_temp": _WhiteTemp.scaled(value, vendor)}
    return _json(_with_transition(payload))

def color(col: Optional[Color], _vendor: Vendor) -> str:
    "Returns a payload to set or retrieve the given hex color."
    if col is None:
        return _json(_with_transition({"color": ""}))
    payload = { "color": { "hex": col.get_hex_l() } }
    return _json(_with_transition(payload))

def start_dim(down: bool, speed: int = DEFAULT_DIMMING_SPEED) -> str:
    "Starts gradually reducing or increasing the brightness."
    factor = -1 if down else 1
    payload = { "brightness_move": factor*speed }
    return _json(payload)

def stop_dim() -> str:
    "Stops gradually changing the brightness."
    payload = { "brightness_move": 0 }
    return _json(payload)

def rename(old: str, new: str) -> str:
    "Returns a payload to rename a device."
    payload = { "from": old, "to": new }
    return _json(payload)

################################################
##### READING
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
    r = 12.92*r if r <= 0.0031308 else (1.0 + 0.055) * pow(r, (1.0 / 2.4)) - 0.055
    g = 12.92*g if g <= 0.0031308 else (1.0 + 0.055) * pow(g, (1.0 / 2.4)) - 0.055
    b = 12.92*b if b <= 0.0031308 else (1.0 + 0.055) * pow(b, (1.0 / 2.4)) - 0.055
    return Color(rgb=(r, g, b))

def _json(payload) -> str:
    "Creates a payload."
    return json.dumps(payload)

def _with_transition(payload, transition_time: Optional[int] = None):
    "Adds a transition specification to the payload"
    transition_time = transition_time or DEFAULT_TRANS
    payload["transition"] = transition_time
    return payload

class _Bright:
    "Deals with brightness values, translates relative brightnesses into absolute values."
    max: int = 254
    min: int = 0

    @staticmethod
    def scaled(scale: float) -> int:
        "Returns the absolute brightness for a scalar ∈ [0,1]."
        return int(_Bright.max*scale)

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
            "diff": 454-250,
        },
        Vendor.Hue: {
            "min":  153,
            "max":  500,
            "diff": 500-153,
        }
    }

    @staticmethod
    def scaled(scale: float, vendor: Vendor) -> float:
        "Returns the absolute brightness for a scalar ∈ [0,1]."
        return _WhiteTemp.cfg[vendor]["diff"]*(1-scale) + _WhiteTemp.cfg[vendor]["min"]

    @staticmethod
    def read(val: int, vendor: Vendor) -> float:
        "Returns the scalar based on the value retrieved from the device."
        upper = _WhiteTemp.cfg[vendor]["diff"]
        val = val - _WhiteTemp.cfg[vendor]["min"]
        return 1-(float(val) / upper)
