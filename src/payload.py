"Everything regarding payloads"

from enum import Enum
from colour import Color

class QoS(Enum):
    "All quality of service specifications"
    ONLY_ONCE = 2
    AT_LEAST_ONCE = 1
    ONCE = 0

class Payload:
    "Constant payloads and functions to create payloads"

    default_transition = 1

    on: str = '{ "state": "ON" }'
    off: str = '{ "state": "OFF" }'
    toggle: str = '{ "state": "TOGGLE" }'

    @staticmethod
    def create(key: str, value: str) -> str:
        "Creates a payload."
        return '{ "' + key + '": "' + value + '", "transition": ' + str(Payload.default_transition) + '}'

    @staticmethod
    def state(value: str) -> str:
        "Creates a payload."
        return '{ "state": "' + value + '" }'

    @staticmethod
    def brightness(value: float) -> str:
        "Returns a payload to set the scaled in [0,1]."
        return Payload.create("brightness", str(Brightness.scaled(value)))

    @staticmethod
    def ikea_color_temp(value: float) -> str:
        "Returns a payload to set the scaled in [0,1]."
        return Payload.create("color_temp", str(ColorTemp.ikea_scaled(value)))

    @staticmethod
    def hue_color_temp(value: float) -> str:
        "Returns a payload to set the scaled in [0,1]."
        return Payload.create("color_temp", str(ColorTemp.hue_scaled(value)))

    @staticmethod
    def color(color: Color) -> str:
        "Returns a payload to set the given hex color."
        return '{ "color": { "hex": "' + str(color.get_hex_l()) + '" }, "transition": ' + str(Payload.default_transition) + ' }'

class Brightness:
    "Deals with brightness values, translates relative brightnesses into absolute values."
    max: int = 254
    min: int = 0

    @staticmethod
    def scaled(scale: float) -> float:
        "Returns the absolute brightness for a scalar ∈ [0,1]."
        return Brightness.max*scale

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
