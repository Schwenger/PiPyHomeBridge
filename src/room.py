"Rooms"

from typing import List, Optional
from light import AbstractLight
from remote import Remote
from light_group import LightGroup
from topic import Topic
from device import DeviceKind, Vendor
import light_types

class Room:
    "A room."

    def __init__(self, name: str, lights: LightGroup, remotes: List[Remote]):
        self.name: str = name
        self.lights: LightGroup = lights
        self.remotes: List[Remote] = remotes

    def find_remote(self, topic: Topic) -> Optional[Remote]:
        "Find the device with the given topic."
        return next((item for item in self.remotes if item.name == topic.name), None)

    def _remote_by_name(self, name: str) -> Optional[Remote]:
        "Finds the light with the given name in the room."
        return next((remote for remote in self.remotes if remote.name == name), None)

def living_room() -> Room:
    "Creates an instance of the living room."
    name = "Living Room"
    abs_lights: List[AbstractLight] = [
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
        abs_lights,
        adaptive=True,
        colorful=True
    )
    remotes = [
        Remote.default_ikea_remote(name, ident="bbbc"),
        Remote.default_dimmer(name, name="Dimmer", ident="bbbb")
    ]
    return Room(name, lights, remotes)

def office() -> Room:
    "Creates an instance of the living room."
    name = "Office"
    abs_lights: List[AbstractLight] = [
        light_types.simple(
            name="Comfort Light",
            room=name,
            kind=DeviceKind.Outlet,
            vendor=Vendor.Ikea,
            ident="aaad",
        )
    ]
    lights = LightGroup(
        abs_lights,
        adaptive=True,
        colorful=True
    )
    remotes = [
        Remote.default_dimmer(name, name="Dimmer", ident="bbbd")
    ]
    return Room(name, lights, remotes)
