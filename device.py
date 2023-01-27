"Definition of devices."

from enum import Enum
from abc import ABC

class Command(Enum):
    "Different Commands"
    GET = "get"
    SET = "set"

TOPIC_BASE = "zigbee2mqtt"

class Device(ABC):
    "Represents a generic device"
    def __init__(self, name: str, room: str, kind: str):
        self.name = name
        self.room = room
        self.kind = kind

    def topic(self, command: str = None) -> str:
        "Creates a topic for the device"
        res = "/".join([TOPIC_BASE, self.room, self.kind, self.name])
        if command is not None:
            res += "/" + command
        return res

    def set_topic(self) -> str:
        "Creates a set-topic for the device"
        return self.topic(Command.SET.value)

    def get_topic(self) -> str:
        "Creates a set-topic for the device"
        return self.topic(Command.GET.value)

