"a"

import math
from typing import List, Callable, Dict
from lights import Light
from light_config import LightConfig

class RoomConfig():
    "b"

    DIM_DELTA = 0.15

    def __init__(
        self,
        lights: List[Light],
        bias: Callable[[Light], int],
        adaptive: bool,
        colorful: bool
    ):
        self.__levels: Dict[Light, int] = dict(map(lambda l: (l, 0), lights))
        self._bias = dict(zip(lights, map(bias, lights)))
        self.adaptive: bool = adaptive
        self.colorful: bool = colorful
        self._hue_offset = 0

    def adapt_config(self, light: Light, cfg: LightConfig) -> LightConfig:
        "c"
        brightness = self.__adapt_brightness(light, cfg)
        cfg.with_brightness(brightness)
        cfg  = cfg.with_hue_offset(self._hue_offset)
        if not self.colorful:
            cfg = cfg.purge_color()
        if not self.adaptive:
            cfg = cfg.purge_dimming()
        return cfg

    def __adapt_brightness(self, light: Light, cfg: LightConfig) -> float:
        delta = self._bias[light] + self.__levels[light]
        if delta == 0:
            return cfg.brightness
        offset = delta * RoomConfig.DIM_DELTA
        new = cfg.brightness + offset
        if 0 <= new <= 1:
            return new
        if new < 0:
            self.__levels[light] = math.ceil(cfg.brightness / RoomConfig.DIM_DELTA)
            return 0
        self.__levels[light] = math.floor((1-cfg.brightness) / RoomConfig.DIM_DELTA)
        return 1

    def shift_color_clockwise(self):
        "Shift color clockwise"
        self._hue_offset += 1

    def shift_color_counter_clockwise(self):
        "Shift color counter clockwise"
        self._hue_offset -= 1

    def dim(self):
        "a"
        for light in self.__levels:
            self.__levels[light] -= 1

    def brighten(self):
        "a"
        for light in self.__levels:
            self.__levels[light] += 1
