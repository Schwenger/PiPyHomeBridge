"Represents a home."

from typing import List, Optional, Tuple

import lighting
from comm import Topic
from device import Addressable
from enums import ApiCommand
from home.room import Room
from homebaseerror import HomeBaseError
from remote import Remote


class Home(Addressable, lighting.Collection):
    "Collection of rooms"

    ROOT_LIGHT_CONFIG = lighting.RootConfig(
        colorful=True,
        dynamic=True,
        static=lighting.State.max()
    )

    def __init__(self, rooms: List[Room]):
        self.rooms = rooms

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

    def remotes(self) -> List[Remote]:
        "Returns all remotes in the home"
        return sum(map(lambda r: r.remotes, self.rooms), [])

    def find_remote(self, topic: Topic) -> Optional[Remote]:
        "Find the remote with the given topic."
        for room in self.rooms:
            for remote in room.remotes:
                if remote.topic == topic:
                    return remote
        return None

    def find_light(self, topic: Topic) -> Optional[lighting.Concrete]:
        "Find the light with the given topic."
        for room in self.rooms:
            for light in room.group.flatten_lights():
                if light.topic == topic:
                    return light
        return None

    def find_abstract_light(self, topic: Topic) -> Optional[lighting.Abstract]:
        "Find the abstract light, so a light or a group for the topic."
        raise NotImplementedError

    def compile_config(self, topic: Topic) -> Optional[lighting.Config]:
        "Compiles the configuration for the light with the given topic if present."
        for room in self.rooms:
            res = room.group.compile_config(topic)
            if res is not None:
                return res
        return None

    def flatten_lights(self) -> List[lighting.Concrete]:
        return sum(map(lambda r: r.group.flatten_lights(), self.rooms), [])
