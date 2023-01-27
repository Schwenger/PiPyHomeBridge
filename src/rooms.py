"Rooms"

from typing import List
from abc import ABC, abstractmethod
from paho.mqtt import client as mqtt
from lights import Light
from remote import Remote
from light_config import LightConfig
from log import trace, info

class Room(ABC):
    "Abstract base class for rooms"

    def __init__(self, name: str, adaptive_dimming: bool = False, colorful: bool = False):
        self.name = name
        self.lights = self._create_lights()
        self.remotes = self._create_remotes()
        self.adaptive_dimming = adaptive_dimming
        self.colorful = colorful
        self.brightness_offset = 0
        self.hue_offset = 0

    @abstractmethod
    def _create_remotes(self) -> List[Remote]:
        pass

    @abstractmethod
    def _create_lights(self) -> List[Light]:
        pass

    def refresh_lights(self, client):
        "Adapts the lights to the current time of day.  Should be called periodically."
        trace(name = self.name, fun = "Refresh lights")
        if self.adaptive_dimming or self.colorful:
            self._apply_config(client, override=False)

    def toggle_lights(self, client: mqtt.Client):
        "toggles all lights"
        trace(name = self.name, fun = "toggle lights")
        for light in self.lights:
            light.toggle(client)

    def lights_on(self, client: mqtt.Client):
        "turn all lights on"
        trace(name = self.name, fun = "lights on")
        self._apply_config(client, override=True)

    def lights_off(self, client: mqtt.Client):
        "turn all lights off"
        trace(name = self.name, fun = "lights off")
        for light in self.lights:
            light.turn_off(client)

    def shift_color_clockwise(self, client: mqtt.Client):
        "Shift color clockwise"
        trace(name = self.name, fun = "shift color clockwise")
        self.hue_offset += 1
        self._apply_config(client, override=False)

    def shift_color_counter_clockwise(self, client: mqtt.Client):
        "Shift color counter clockwise"
        trace(name = self.name, fun = "shift color counter clockwise")
        self.hue_offset -= 1
        self._apply_config(client, override=False)

    def dim(self, client: mqtt.Client):
        "Dim the lights in the room"
        trace(name = self.name, fun = "dim")
        self.brightness_offset = max(self.brightness_offset - 1, -4)
        self._apply_config(client, override=False)

    def brighten(self, client: mqtt.Client):
        "Brighten the lights in the room"
        trace(name = self.name, fun = "brighten")
        self.brightness_offset = min(self.brightness_offset + 1, 4)
        self._apply_config(client, override=False)

    def enable_adaptive_dimming(self, client: mqtt.Client):
        "Enables AdaptiveDimming"
        trace(name = self.name, fun = "enable adaptive dimming")
        self.adaptive_dimming = True
        self.refresh_lights(client)

    def disable_adaptive_dimming(self, client: mqtt.Client):
        "Disables AdaptiveDimming"
        trace(name = self.name, fun = "disable adaptive dimming")
        self.adaptive_dimming = False
        self.refresh_lights(client)

    def enable_colorful(self, client: mqtt.Client):
        "Enables Colorful"
        trace(name = self.name, fun = "enable colorful")
        self.colorful = True
        self.refresh_lights(client)

    def disable_colorful(self, client: mqtt.Client):
        "Disables Colorful"
        trace(name = self.name, fun = "disable colorful")
        self.colorful = False
        self.refresh_lights(client)

    def random_effect1(self, client: mqtt.Client):
        "Triggers an effect, yay"
        # {"effect": NEW_VALUE}.
        # The possible values are:
        # blink, breathe, okay, channel_change, candle,
        # fireplace, colorloop, finish_effect,
        # stop_effect, stop_hue_effect.
        # {"effect": NEW_VALUE}.
        # The possible values are: blink, breathe,
        # okay, channel_change, finish_effect, stop_effect

    def random_effect2(self, client: mqtt.Client):
        "Triggers an effect, yay"

    def _apply_config(self, client: mqtt.Client, override: bool, cfg: LightConfig = None):
        trace(name = self.name, fun = "_apply config")
        for light in self.lights:
            if cfg is None:
                cfg = self._get_config()
            changes_on_off_status = light.is_on() != cfg.is_on
            if changes_on_off_status and not override:
                continue
            light.apply_config(client, cfg)

    def _get_config(self) -> LightConfig:
        "Returns the appropriate LightConfig for the given light, time of day, and LightFlow state."
        trace(name = self.name, fun = "get config")
        cfg = LightConfig.recommended()
        cfg = cfg.offset_by(brightness=self.brightness_offset, hue=self.hue_offset)
        if not self.colorful:
            cfg = cfg.purge_color()
        if not self.adaptive_dimming:
            cfg = cfg.purge_dimming()
        return cfg

class LivingRoom(Room):
    "Everything concerning the Living Room"

    def __init__(self):
        super().__init__("Living Room", adaptive_dimming=True, colorful=True)

    def _create_remotes(self):
        return [ Remote.default_ikea_remote(self) ]

    def _create_lights(self):
        return [
            Light.simple(  "Comfort Light",     self.name, kind="Outlet"),
            Light.dimmable("Uplight/Reading",   self.name),
            Light.color(   "Uplight/Main",      self.name),
            Light.color(   "Orb",               self.name),
        ]

class Office(Room):
    "Everything concerning the Office"

    def __init__(self):
        super().__init__("Office")

    def _create_remotes(self) -> List[Remote]:
        return [ Remote.default_dimmer(self) ]

    def _create_lights(self) -> List[Light]:
        return [ Light.simple("Comfort Light", self.name, kind="Outlet") ]

class Home():
    "Collection of rooms"

    def __init__(self):
        self.rooms = [
            LivingRoom(),
            # Office()
        ]

    def refresh_lights(self, client):
        "Adapts the lights to the current time of day.  Should be called periodically."
        for room in self.rooms:
            room.refresh_lights(client)

    def remotes(self) -> List[Remote]:
        "Returns all remotes in the home"
        res = []
        for room in self.rooms:
            res += room.remotes
        return res

    def lights(self) -> List[Light]:
        "Returns all lights in the home"
        res = []
        for room in self.rooms:
            res += room.lights
