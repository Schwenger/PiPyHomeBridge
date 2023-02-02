"Everything regarding payloads"

from enum import Enum
from typing import Optional
import json
from colour import Color

class QoS(Enum):
    "All quality of service specifications"
    ONLY_ONCE = 2
    AT_LEAST_ONCE = 1
    ONCE = 0

DEFAULT_TRANS = 1

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

def state(value: str) -> str:
    "Creates a payload for a state change."
    return _json(with_transition({"state" : value}))

def brightness(value: float) -> str:
    "Returns a payload to set the scaled in [0,1]."
    return _json(with_transition({"brightness": Bright.scaled(value)}))

@staticmethod
def ikea_color_temp(value: float) -> str:
    "Returns a payload to set the scaled in [0,1]."
    return _json(with_transition({"color_temp": ColorTemp.ikea_scaled(value)}))

def hue_color_temp(value: float) -> str:
    "Returns a payload to set the scaled in [0,1]."
    return _json(with_transition({"color_temp": ColorTemp.hue_scaled(value)}))

@staticmethod
def color(col: Color) -> str:
    "Returns a payload to set the given hex color."
    payload = { "color": { "hex": col.get_hex_l() } }
    return _json(with_transition(payload))

class Bright:
    "Deals with brightness values, translates relative brightnesses into absolute values."
    max: int = 254
    min: int = 0

    @staticmethod
    def scaled(scale: float) -> float:
        "Returns the absolute brightness for a scalar ∈ [0,1]."
        return Bright.max*scale

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
        offset = ColorTemp.hue_min + ColorTemp.hue_bias
        return (ColorTemp.hue_max - (offset))*(1-scale) + offset
