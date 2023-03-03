"Rooms"

from typing import List, Optional
from paho.mqtt import client as mqtt
from light import AbstractLight
from remote import Remote
from light_group import LightGroup
from topic import Topic
from queue_data import ApiCommand
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
            kind=DeviceKind.Outlet
        ),
        light_types.dimmable(name="Uplight/Reading", room=name, vendor=Vendor.Ikea),
        light_types.white(   name="Uplight/Main",    room=name, vendor=Vendor.Hue),
        light_types.color(   name="Orb",             room=name, vendor=Vendor.Hue),
    ]
    lights = LightGroup(
        abs_lights,
        adaptive=True,
        colorful=True
    )
    remotes = [
        Remote.default_ikea_remote(name),
        Remote.default_dimmer(name)
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
            vendor=Vendor.Ikea
        )
    ]
    lights = LightGroup(
        abs_lights,
        adaptive=True,
        colorful=True
    )
    remotes = [
        Remote.default_dimmer(name)
    ]
    return Room(name, lights, remotes)

class Home():
    "Collection of rooms"

    def __init__(self):
        self.rooms = [
            living_room(),
            office()
        ]

    def remote_action(self, remote: Topic, action: str) -> Optional[ApiCommand]:
        "Attempts to determine the api command represented by the action of the given remote."
        device = self.find_remote(remote)
        assert device is not None
        cmd = device.cmd_for_action(action)
        print(f"Button pressed: {action}, ApiCommand: {cmd}.")
        return cmd

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

    def lights(self) -> List[AbstractLight]:
        "Returns all lights in the home"
        return sum(map(lambda r: r.lights.lights, self.rooms), [])

    def find_remote(self, topic: Topic) -> Optional[Remote]:
        "Find the device with the given topic."
        for room in self.rooms:
            if room.name == topic.room:
                return room.find_remote(topic)
        return None
