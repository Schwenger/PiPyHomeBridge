"Definition of devices."

from abc import ABC
from topic import Topic
from enums import DeviceKind, Vendor

TOPIC_BASE = "zigbee2mqtt"

class Device(ABC):
    "Represents a generic device"
    def __init__(self, name: str, room: str, kind: DeviceKind, vendor: Vendor):
        self.name = name
        self.room = room
        self.kind = kind
        self.vendor = vendor
        self.topic = Topic.for_device(name=self.name, kind=self.kind, groups=[])

    def set_topic(self) -> str:
        "Creates a set-topic for the device"
        return self.topic.as_set()

    def get_topic(self) -> str:
        "Creates a set-topic for the device"
        return self.topic.as_get()
