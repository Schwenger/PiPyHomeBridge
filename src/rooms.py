"Rooms"

from typing import List, Optional
from abc import ABC, abstractmethod
from paho.mqtt import client as mqtt
import lights
from lights import Light
from remote import Remote
from light_config import LightConfig, Brightness
from log import trace

class Room(ABC):
    "Abstract base class for rooms"

    def __init__(self, name: str, adaptive_dimming: bool = False, colorful: bool = False):
        self.name: str = name
        self.lights: List[Light] = self._create_lights()
        self.remotes: List[Remote] = self._create_remotes()
        self.adaptive_dimming: bool = adaptive_dimming
        self.colorful: bool = colorful
        self.dim_level: Brightness = Brightness.NEUTRAL
        self.hue_offset: int = 0
        self.is_on: bool = True

    @abstractmethod
    def _create_remotes(self) -> List[Remote]:
        pass

    @abstractmethod
    def _create_lights(self) -> List[Light]:
        pass

    @abstractmethod
    def _bias_for(self, light: Light) -> int:
        "Defines the bias for a given light."

    def refresh_lights(self, client):
        "Adapts the lights to the current time of day.  Should be called periodically."
        trace(name = self.name, fun = "Refresh lights")
        self._apply_config(client, override_on_off=False)

    def toggle_lights(self, client: mqtt.Client):
        "toggles all lights"
        trace(name = self.name, fun = "toggle lights")
        for light in self.lights:
            light.toggle(client)

    def lights_on(self, client: mqtt.Client):
        "turn all lights on"
        trace(name = self.name, fun = "lights on")
        self._apply_config(client, override_on_off=True)

    def lights_off(self, client: mqtt.Client):
        "turn all lights off"
        trace(name = self.name, fun = "lights off")
        for light in self.lights:
            light.turn_physically_off(client)

    def shift_color_clockwise(self, client: mqtt.Client):
        "Shift color clockwise"
        trace(name = self.name, fun = "shift color clockwise")
        self.hue_offset += 1
        self.refresh_lights(client)

    def shift_color_counter_clockwise(self, client: mqtt.Client):
        "Shift color counter clockwise"
        trace(name = self.name, fun = "shift color counter clockwise")
        self.hue_offset -= 1
        self.refresh_lights(client)

    def dim(self, client: mqtt.Client):
        "Dim the lights in the room"
        trace(name = self.name, fun = "dim")
        self.dim_level = self.dim_level.dec()
        self.refresh_lights(client)

    def brighten(self, client: mqtt.Client):
        "Brighten the lights in the room"
        trace(name = self.name, fun = "brighten")
        self.dim_level = self.dim_level.inc()
        self.refresh_lights(client)

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

    def _apply_config(
            self,
            client: mqtt.Client,
            override_on_off: bool,
            cfg: Optional[LightConfig] = None
        ):
        trace(name = self.name, fun = "_apply config")
        for light in self.lights:
            target_cfg = cfg or self._get_current_config(light)
            changes_on_off_status = light.is_on() != target_cfg.is_on
            if changes_on_off_status and not override_on_off:
                continue
            light.apply_config(client, target_cfg)

    def _get_current_config(self, light: Light) -> LightConfig:
        "Returns the appropriate LightConfig for the given light, time of day, and LightFlow state."
        trace(name = self.name, fun = "get config")
        cfg  = LightConfig.recommended()
        bias = self._bias_for(light)
        dim  = self.dim_level.with_bias(bias)

        cfg  = cfg.with_dim_level(dim)
        cfg  = cfg.with_hue_offset(self.hue_offset)
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
            lights.create_simple(    "Comfort Light",     self.name, kind="Outlet"),
            lights.create_dimmable(  "Uplight/Reading",   self.name),
            lights.create_white_spec("Uplight/Main",      self.name),
            lights.create_color(     "Orb",               self.name),
        ]

    def _bias_for(self, light: Light) -> int:
        if "Orb" in light.name:
            return +1
        if "Comfort Light" in light.name:
            return -1
        return 0

class Office(Room):
    "Everything concerning the Office"

    def __init__(self):
        super().__init__("Office")

    def _create_remotes(self) -> List[Remote]:
        return [ Remote.default_dimmer(self) ]

    def _create_lights(self) -> List[Light]:
        return [ lights.create_simple("Comfort Light", self.name, kind="Outlet") ]

    def _bias_for(self, light: Light) -> int:
        return 0

class Home():
    "Collection of rooms"

    def __init__(self):
        self.rooms = [
            LivingRoom(),
            Office()
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
        return res
