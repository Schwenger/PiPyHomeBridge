"Definition of devices."

from enum import Enum
from abc import ABC
from payload import Topic

class Command(Enum):
    "Different Commands"
    GET = "get"
    SET = "set"

TOPIC_BASE = "zigbee2mqtt"

class Device(ABC):
    "Represents a generic device"
    def __init__(self, name: str, room: str, kind: str, vendor: str):
        self.name = name
        self.room = room
        self.kind = kind
        self.vendor = vendor
        self.topic = Topic(name=self.name, room=self.room, device=self.kind)

    def set_topic(self) -> str:
        "Creates a set-topic for the device"
        return self.topic.as_set()

    def get_topic(self) -> str:
        "Creates a set-topic for the device"
        return self.topic.as_get()
