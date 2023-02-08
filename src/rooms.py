"Rooms"

from typing import List, Optional
from abc import ABC, abstractmethod
from paho.mqtt import client as mqtt
import lights
from lights import Light
from remote import Remote
from light_collection import LightCollection
from payload import RoutingResult, Topic

class Room(ABC, LightCollection):
    "Abstract base class for rooms"

    def __init__(self, name: str, adaptive: bool = False, colorful: bool = False):
        self.name: str = name
        super().__init__(self._create_lights(), adaptive=adaptive, colorful=colorful)
        self.remotes: List[Remote] = self._create_remotes()

    @abstractmethod
    def _create_remotes(self) -> List[Remote]:
        pass

    @abstractmethod
    def _create_lights(self) -> List[Light]:
        pass

    def find_remote(self, topic: Topic) -> Optional[Remote]:
        "Find the device with the given topic."
        return next((item for item in self.remotes if item.name == topic.name), None)

    def route_message(self, client: mqtt.Client, topic: Topic, payload) -> RoutingResult:
        "Routes the message to the device based on the topic."
        light_res = LightCollection.route_message(self, client, topic, payload)
        if light_res is not RoutingResult.NOT_FOUND:
            return light_res
        remote = self._remote_by_name(topic.name)
        if remote is not None:
            remote.consume_message(client, payload)
            return RoutingResult.ACCEPT
        return RoutingResult.NOT_FOUND

    def _remote_by_name(self, name: str) -> Optional[Remote]:
        "Finds the light with the given name in the room."
        return next((remote for remote in self.remotes if remote.name == name), None)

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
