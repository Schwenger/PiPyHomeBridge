"Represents a home."

from typing import Optional, List, Tuple
from paho.mqtt import client as mqtt
from lights.interface import AbstractLight, Light
from enums import ApiCommand, HomeBaseError
from home.room import living_room, office, Room
from home.topic import Topic
from home.remote import Remote
from home.device import Addressable


class Home(Addressable):
    "Collection of rooms"

    def __init__(self):
        self.rooms = [
            living_room(),
            office()
        ]

    @property
    def topic(self) -> Topic:
        return Topic.for_home()

    def remote_action(self, remote: Topic, action: str) -> Optional[Tuple[ApiCommand, Topic]]:
        "Attempts to determine the api command represented by the action of the given remote."
        device = self.find_remote(remote)
        if device is None:
            raise HomeBaseError.RemoteNotFound
        cmd = device.cmd_for_action(action)
        if cmd is None:
            return None
        return (cmd, device.controls_topic)

    def room_by_name(self, name: str) -> Optional[Room]:
        "Finds the room with the given name in the home."
        return next((room for room in self.rooms if room.name == name), None)

    def refresh_lights(self, client: mqtt.Client):
        "Adapts the lights to the current time of day.  Should be called periodically."
        for room in self.rooms:
            room.group.refresh(client)

    def remotes(self) -> List[Remote]:
        "Returns all remotes in the home"
        return sum(map(lambda r: r.remotes, self.rooms), [])

    def flatten_lights(self) -> List[Light]:
        "Returns all lights in the home"
        return sum(map(lambda r: r.lights.flatten_lights(), self.rooms), [])

    def find_remote(self, topic: Topic) -> Optional[Remote]:
        "Find the remote with the given topic."
        for room in self.rooms:
            for remote in room.remotes:
                if remote.topic == topic:
                    return remote
        return None

    def find_light(self, topic: Topic) -> Optional[Light]:
        "Find the light with the given topic."
        for room in self.rooms:
            for light in room.group.flatten_lights():
                if light.topic == topic:
                    return light
        return None

    def find_abstract_light(self, topic: Topic) -> Optional[AbstractLight]:
        "Find the abstract light, so a light or a group for the topic."
        raise NotImplementedError
