"Represents a home."

from typing import Optional, List, Tuple
from paho.mqtt import client as mqtt
from room import living_room, office, Room
from topic import Topic
from enums import ApiCommand
from remote import Remote
from light import AbstractLight, Light
from light_group import LightGroup
from device import Addressable

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
        assert device is not None
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
            room.lights.refresh(client)

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
            for light in room.lights.flatten_lights():
                if light.topic == topic:
                    return light
        return None

    def find_abstract_light(self, topic: Topic) -> Optional[AbstractLight]:
        "Find the abstract light, so a light or a group for the topic."
        raise NotImplementedError

    def structure(self):
        "Returns the structure of the home as dict of strings."
        def group_structure(group: LightGroup):
            single = list(map(
                lambda l: {
                    "name": l.name,
                    "id": l.ident,
                    "topic": l.topic.string
                },
                room.lights.single_lights
            ))
            return {
                "name": group.name,
                "singleLights": single,
                "groups": list(map(group_structure, group.groups)),
            }
        rooms = []
        for room in self.rooms:
            remotes = list(map(
                lambda r: { "name": r.name, "id": r.ident, "topic": r.topic.string },
                room.remotes
            ))
            rooms.append({
                "name":     room.name,
                "lights":   group_structure(room.lights),
                "remotes":  remotes,
            })
        return {
            "rooms": rooms,
        }
