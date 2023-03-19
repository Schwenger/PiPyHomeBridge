"Rooms"

from typing import List, Optional

from comm.enums import DeviceModel
from comm.topic import Topic
from home.device import Addressable
from home.remote import Remote
from lighting import Concrete as ConcreteLight, Group as LightGroup
import lighting


class Room(Addressable):
    "A room."

    def __init__(self, name: str, group: LightGroup, remotes: List[Remote]):
        self.name: str = name
        self.group: LightGroup = group
        self.remotes: List[Remote] = remotes

    @property
    def topic(self) -> Topic:
        return Topic.for_room(self.name)

    def find_remote(self, topic: Topic) -> Optional[Remote]:
        "Find the device with the given topic."
        return next((item for item in self.remotes if item.name == topic.name), None)

    def _remote_by_name(self, name: str) -> Optional[Remote]:
        "Finds the light with the given name in the room."
        return next((remote for remote in self.remotes if remote.name == name), None)


def living_room() -> Room:
    "Creates an instance of the living room."
    name = "Living Room"
    lights_list: List[ConcreteLight] = [
        lighting.simple(
            name="Comfort Light",
            room=name,
            model=DeviceModel.IkeaOutlet,
            ident="aaaa",
        ),
        lighting.dimmable(
            name="Uplight/Reading",
            room=name,
            model=DeviceModel.IkeaDimmable,
            ident="aaab",
        ),
        lighting.white(
            name="Uplight/Main",
            room=name,
            model=DeviceModel.HueColor,
            ident="aaac",
        ),
        lighting.color(
            name="Orb",
            room=name,
            model=DeviceModel.HueColor,
            ident="aaad"
        ),
    ]
    lights = lighting.Group(
        name="Main",
        single_lights=lights_list,
        adaptive=True,
        colorful=True,
        hierarchie=[name],
        groups=[]
    )
    room_topic = Topic.for_room(name)
    remotes = [
        Remote.default_ikea_remote(name, controls=room_topic, ident="bbbc"),
        Remote.default_dimmer(name, controls=room_topic, name="Dimmer", ident="bbbb")
    ]
    return Room(name, lights, remotes)


def office() -> Room:
    "Creates an instance of the living room."
    name = "Office"
    lights_list: List[ConcreteLight] = [
        lighting.simple(
            name="Comfort Light",
            room=name,
            model=DeviceModel.IkeaOutlet,
            ident="aaad",
        )
    ]
    lights = lighting.Group(
        name="Main",
        single_lights=lights_list,
        adaptive=True,
        colorful=True,
        hierarchie=[name],
        groups=[]
    )
    room_topic = Topic.for_room(name)
    remotes = [
        Remote.default_dimmer(name, controls=room_topic, name="Dimmer", ident="bbbd")
    ]
    return Room(name, lights, remotes)
