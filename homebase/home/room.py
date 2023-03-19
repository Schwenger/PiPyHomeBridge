"Rooms"

from typing import List, Optional

import lighting
from comm.topic import Topic
from enums import DeviceModel
from home.device import Addressable
from home.remote import Remote
from lighting import Concrete as ConcreteLight
from lighting import FullConfig
from lighting import Group as LightGroup
from lighting import RelativeConfig


class Room(Addressable):
    "A room."

    def __init__(self, name: str, group: LightGroup, remotes: List[Remote]):
        self.name: str = name
        self.group: LightGroup = group
        self.remotes: List[Remote] = remotes

    @property
    def topic(self) -> Topic:
        return Topic.for_room(self.name)

    @property
    def defined_full_config(self) -> Optional[FullConfig]:
        "Returns a full config if defined."
        return self.group.defined_full_config

    @property
    def relative_config(self) -> RelativeConfig:
        "Returns which values are currently overridden."
        return self.group.relative_config

    def find_remote(self, topic: Topic) -> Optional[Remote]:
        "Find the device with the given topic."
        return next((item for item in self.remotes if item.name == topic.name), None)

    def _remote_by_name(self, name: str) -> Optional[Remote]:
        "Finds the light with the given name in the room."
        return next((remote for remote in self.remotes if remote.name == name), None)

    ################################################
    # CONFIGURATIVE API
    ################################################
    def set_full_config(self, config: FullConfig):
        "Sets the full config."
        self.group.set_full_config(config)

    def inherit_config(self):
        "Invalidates the full config and inherits from parent entities."
        self.group.inherit_config()

    def set_relative_config(self, config: RelativeConfig):
        "Sets the relative config."
        self.group.set_relative_config(config)


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
        hierarchie=[name],
        groups=[]
    )
    lights.set_full_config(FullConfig(brightness=1, dynamic=False))
    room_topic = Topic.for_room(name)
    remotes = [
        Remote.default_dimmer(name, controls=room_topic, name="Dimmer", ident="bbbd")
    ]
    return Room(name, lights, remotes)
