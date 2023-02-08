"Rooms"

from typing import List, Optional
from abc import ABC, abstractmethod
from paho.mqtt import client as mqtt
import lights
from lights import Light
from remote import Remote
from light_config import LightConfig
from room_config import RoomConfig
from log import trace
from payload import RoutingResult, Topic

class Room(ABC):
    "Abstract base class for rooms"

    def __init__(self, name: str, adaptive: bool = False, colorful: bool = False):
        self.name: str = name
        self.lights: List[Light] = self._create_lights()
        self.remotes: List[Remote] = self._create_remotes()
        self.room_config: RoomConfig = RoomConfig(
            self.lights,
            self._bias_for,
            adaptive=adaptive,
            colorful=colorful
        )

    @abstractmethod
    def _create_remotes(self) -> List[Remote]:
        pass

    @abstractmethod
    def _create_lights(self) -> List[Light]:
        pass

    @abstractmethod
    def _bias_for(self, light: Light) -> int:
        "Defines the bias for a given light."

    def _light_by_name(self, name: str) -> Optional[Light]:
        "Finds the light with the given name in the room."
        return next((light for light in self.lights if light.name == name), None)

    def _remote_by_name(self, name: str) -> Optional[Remote]:
        "Finds the light with the given name in the room."
        return next((remote for remote in self.remotes if remote.name == name), None)

    def find_light(self, topic: Topic) -> Optional[Light]:
        "Find the device with the given topic."
        return next((item for item in self.lights if item.name == topic.name), None)

    def find_remote(self, topic: Topic) -> Optional[Remote]:
        "Find the device with the given topic."
        return next((item for item in self.remotes if item.name == topic.name), None)

    def route_message(self, client: mqtt.Client, topic: Topic, payload) -> RoutingResult:
        "Routes the message to the device based on the topic."
        light = self._light_by_name(topic.name)
        if light is not None:
            light.consume_message(client, payload)
            return RoutingResult.ACCEPT
        remote = self._remote_by_name(topic.name)
        if remote is not None:
            remote.consume_message(client, payload)
            return RoutingResult.ACCEPT
        return RoutingResult.NOT_FOUND

    def refresh_lights(self, client, override_on_off: bool = False):
        "Adapts the lights to the current time of day.  Should be called periodically."
        trace(name = self.name, fun = "Refresh lights")
        self._apply_config(client, override_on_off)

    def _any_on(self):
        "Returns whether at least on light is on."
        return any(map(Light.is_on, self.lights))

    def toggle_lights(self, client: mqtt.Client):
        "toggles all lights"
        trace(name = self.name, fun = "toggle lights")
        if self._any_on():
            self._apply_config(client, override_on_off=True, cfg=LightConfig.off())
        else:
            self.refresh_lights(client, override_on_off=True)

    def lights_on(self, client: mqtt.Client):
        "turn all lights on"
        trace(name = self.name, fun = "lights on")
        if not self._any_on():
            self.refresh_lights(client, override_on_off=True)

    def lights_off(self, client: mqtt.Client):
        "turn all lights off"
        trace(name = self.name, fun = "lights off")
        if self._any_on():
            self._apply_config(client, override_on_off=True, cfg=LightConfig.off())

    def shift_color_clockwise(self, client: mqtt.Client):
        "Shift color clockwise"
        trace(name = self.name, fun = "shift color clockwise")
        self.room_config.shift_color_clockwise()
        self.refresh_lights(client)

    def shift_color_counter_clockwise(self, client: mqtt.Client):
        "Shift color counter clockwise"
        trace(name = self.name, fun = "shift color counter clockwise")
        self.room_config.shift_color_counter_clockwise()
        self.refresh_lights(client)

    def dim(self, client: mqtt.Client):
        "Dim the lights in the room"
        trace(name = self.name, fun = "dim")
        self.room_config.dim()
        self.refresh_lights(client)

    def brighten(self, client: mqtt.Client):
        "Brighten the lights in the room"
        trace(name = self.name, fun = "brighten")
        self.room_config.brighten()
        self.refresh_lights(client)

    def start_dim_down(self, client: mqtt.Client):
        "Starts dimming the lights"
        trace(name = self.name, fun="start_dim_down")
        for light in self.lights:
            light.start_dim_down(client)

    def start_dim_up(self, client: mqtt.Client):
        "Starts dimming the lights"
        trace(name = self.name, fun="start_dim_up")
        for light in self.lights:
            light.start_dim_up(client)

    def stop_dim(self, client: mqtt.Client):
        "Stops dimming the lights"
        trace(name = self.name, fun="stop_dim")
        for light in self.lights:
            light.stop_dim(client)

    def enable_adaptive_dimming(self, client: mqtt.Client):
        "Enables AdaptiveDimming"
        trace(name = self.name, fun = "enable adaptive dimming")
        self.room_config.adaptive = True
        self.refresh_lights(client)

    def disable_adaptive_dimming(self, client: mqtt.Client):
        "Disables AdaptiveDimming"
        trace(name = self.name, fun = "disable adaptive dimming")
        self.room_config.adaptive = False
        self.refresh_lights(client)

    def enable_colorful(self, client: mqtt.Client):
        "Enables Colorful"
        trace(name = self.name, fun = "enable colorful")
        self.room_config.colorful = True
        self.refresh_lights(client)

    def disable_colorful(self, client: mqtt.Client):
        "Disables Colorful"
        trace(name = self.name, fun = "disable colorful")
        self.room_config.colorful = False
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
        cfg = self.room_config.adapt_config(light, cfg)
        return cfg

class LivingRoom(Room):
    "Everything concerning the Living Room"

    def __init__(self):
        super().__init__("Living Room", adaptive=True, colorful=True)

    def _create_remotes(self):
        return [
            Remote.default_ikea_remote(self),
            Remote.default_dimmer(self)
        ]

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

    def route_message(self, client: mqtt.Client, topic: Topic, data) -> RoutingResult:
        "Routes the message to the room and device based on the topic."
        for room in self.rooms:
            if room.name == topic.room:
                res = room.route_message(client, topic, data)
                if res in { RoutingResult.ACCEPT,  RoutingResult.REJECT }:
                    return res
                ValueError(res)
        return RoutingResult.NOT_FOUND

    def find_light(self, topic: Topic) -> Optional[Light]:
        "Find the device with the given topic."
        for room in self.rooms:
            if room.name == topic.room:
                return room.find_light(topic)
        return None

    def find_remote(self, topic: Topic) -> Optional[Remote]:
        "Find the device with the given topic."
        for room in self.rooms:
            if room.name == topic.room:
                return room.find_remote(topic)
        return None
