"Rooms"

from typing import List, Optional
from light import Light
from remote import Remote
from light_group import LightGroup
from topic import Topic
from device import DeviceKind, Vendor, Addressable
import light_types

class Room(Addressable):
    "A room."

    def __init__(self, name: str, lights: LightGroup, remotes: List[Remote]):
        self.name: str = name
        self.lights: LightGroup = lights
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
    lights_list: List[Light] = [
        light_types.simple(
            name="Comfort Light",
            room=name,
            vendor=Vendor.Ikea,
            kind=DeviceKind.Outlet,
            ident="aaaa",
        ),
        light_types.dimmable(
            name="Uplight/Reading",
            room=name,
            vendor=Vendor.Ikea,
            ident="aaab",
        ),
        light_types.white(
            name="Uplight/Main",
            room=name,
            vendor=Vendor.Hue,
            ident="aaac",
        ),
        light_types.color(
            name="Orb",
            room=name,
            vendor=Vendor.Hue,
            ident="aaad"
        ),
    ]
    lights = LightGroup(
        name="Main",
        single_lights = lights_list,
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
    lights_list: List[Light] = [
        light_types.simple(
            name="Comfort Light",
            room=name,
            kind=DeviceKind.Outlet,
            vendor=Vendor.Ikea,
            ident="aaad",
        )
    ]
    lights = LightGroup(
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
