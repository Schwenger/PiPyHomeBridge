"Everything regarding payloads"

from enum import Enum
from typing import Optional, List
import json
from colour import Color

class QoS(Enum):
    "All quality of service specifications"
    ONLY_ONCE = 2
    AT_LEAST_ONCE = 1
    ONCE = 0

DEFAULT_TRANS = 1
DEFAULT_DIMMING_SPEED = 40

on: str = '{ "state": "ON" }'
off: str = '{ "state": "OFF" }'
toggle: str = '{ "state": "TOGGLE" }'

def _json(payload) -> str:
    "Creates a payload."
    return json.dumps(payload)

def with_transition(payload, transition_time: Optional[int] = None):
    "Adds a transition specification to the payload"
    transition_time = transition_time or DEFAULT_TRANS
    payload["transition"] = transition_time
    return payload

def state(value: Optional[str]) -> str:
    "Creates a payload for a state change."
    return _json(with_transition({"state" : value or ""}))

def brightness(value: Optional[float]) -> str:
    "Returns a payload to set the scaled in [0,1]."
    if value is None:
        return _json(with_transition({"brightness": ""}))
    return _json(with_transition({"brightness": Bright.scaled(value)}))

def ikea_color_temp(value: float) -> str:
    "Returns a payload to set the scaled in [0,1]."
    return _json(with_transition({"color_temp": ColorTemp.ikea_scaled(value)}))

def hue_color_temp(value: float) -> str:
    "Returns a payload to set the scaled in [0,1]."
    return _json(with_transition({"color_temp": ColorTemp.hue_scaled(value)}))

def color(col: Color) -> str:
    "Returns a payload to set the given hex color."
    payload = { "color": { "hex": col.get_hex_l() } }
    return _json(with_transition(payload))

def start_dim_down(speed: int = DEFAULT_DIMMING_SPEED) -> str:
    payload = { "brightness_move": -speed }
    return _json(payload)

def start_dim_up(speed: int = DEFAULT_DIMMING_SPEED) -> str:
    payload = { "brightness_move": +speed }
    return _json(payload)

def stop_dim() -> str:
    payload = { "brightness_move": 0 }
    return _json(payload)

def transform_brightness(val: str) -> float:
    "Returns the white temperature as scale based on the value retrieved from the device."
    return Bright.from_device(int(val))

def transform_state(val: str) -> bool:
    "Returns the white temperature as scale based on the value retrieved from the device."
    return val == "ON"

def transform_white_temp(val: str, vendor: str) -> float:
    "Returns the white temperature as scale based on the value retrieved from the device."
    if vendor == "hue":
        return ColorTemp.hue_from_device(int(val))
    if vendor == "ikea":
        return ColorTemp.ikea_from_device(int(val))
    raise ValueError(vendor)

def transform_color(x: float, y: float, Y: float) -> Color:
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

class Bright:
    "Deals with brightness values, translates relative brightnesses into absolute values."
    max: int = 254
    min: int = 0

    @staticmethod
    def scaled(scale: float) -> float:
        "Returns the absolute brightness for a scalar ∈ [0,1]."
        return Bright.max*scale

    @staticmethod
    def from_device(val: int) -> float:
        "Returns the scalar based on the value retrieved from the device."
        return float(val) / Bright.max

class ColorTemp:
    "Deals with white color temperature"
    ikea_max: int = 454
    ikea_min: int = 250
    hue_max: int = 500
    hue_min: int = 153
    hue_bias: int = 300

    @staticmethod
    def ikea_scaled(scale: float) -> float:
        "Returns the absolute brightness for a scalar ∈ [0,1]."
        return (ColorTemp.ikea_max - ColorTemp.ikea_min)*scale

    @staticmethod
    def hue_scaled(scale: float) -> float:
        "Returns the absolute brightness for a scalar ∈ [0,1]."
        return (ColorTemp.hue_max - ColorTemp.hue_min)*(1-scale) + ColorTemp.hue_min

    @staticmethod
    def hue_from_device(val: int) -> float:
        "Returns the scalar based on the value retrieved from the hue device."
        upper = ColorTemp.hue_max - ColorTemp.hue_min
        val = val - ColorTemp.hue_min
        return 1-(float(val) / upper)

    @staticmethod
    def ikea_from_device(val: int) -> float:
        "Returns the scalar based on the value retrieved from the ikea device."
        upper = ColorTemp.ikea_max - ColorTemp.ikea_min
        val = val - ColorTemp.ikea_min
        return float(val) / upper

class Topic:
    """
    Represents topics in the zigbee protocol.
    Starts with a base, followed by a room and the name of the object.
    Might be extended in the future.
    """
    BASE = "zigbee2mqtt"
    SEP = "/"
    def __init__(self, room: str, physical_kind: str, name: str):
        self.room = room
        self.physical_kind = physical_kind
        self.name = name
        self.str = self._join([Topic.BASE, room, physical_kind, name])

    @staticmethod
    def _join(parts: List[str]) -> str:
        return "/".join(parts)

    def as_set(self) -> str:
        "Returns this topic as a set-command."
        return self.str + Topic.SEP + "set"

    def as_get(self) -> str:
        "Returns this topic as a get-command."
        return self.str + Topic.SEP + "get"

    @staticmethod
    def from_str(string: str) -> 'Topic':
        "Creates a topic from a string.  Asserts proper format. May not be a command."
        split = string.split(Topic.SEP)
        assert split[0] == Topic.BASE
        assert split[-1] not in ["set", "get"]
        name = Topic._join(split[3:])
        return Topic(room=split[1], physical_kind=split[2], name=name)

class RoutingResult(Enum):
    "The result of a routing attempt"
    ACCEPT = 1
    NOT_FOUND = 2
    REJECT = 3
