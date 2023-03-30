"Rooms"

from typing import List, Optional

import lighting
from comm import Topic
from device import Addressable
from remote import Remote

class Room(Addressable, lighting.Collection):
    "A room."

    def __init__(self, name: str, group: lighting.Group, remotes: List[Remote]):
        self.name: str = name
        self.group: lighting.Group = group
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

    def flatten_lights(self) -> List[lighting.Concrete]:
        return self.group.flatten_lights()
