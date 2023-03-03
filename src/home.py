"Represents a home."

from typing import Optional, List
from paho.mqtt import client as mqtt
from room import living_room, office, Room
from topic import Topic
from enums import ApiCommand
from remote import Remote
from light import AbstractLight

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
