"Definition of devices."

from abc import ABC, abstractmethod
from topic import Topic
from enums import DeviceKind, Vendor

TOPIC_BASE = "zigbee2mqtt"

class Addressable(ABC):
    "Marks an entity as addressable."

    @property
    @abstractmethod
    def topic(self) -> Topic:
        "Returns the topic to address this entity"

class Device(Addressable, ABC):
    "Represents a generic device"

    def __init__(self,
        name: str,
        room: str,
        kind: DeviceKind,
        vendor: Vendor,
        ident: str,
    ):
        self.name = name
        self.room = room
        self.kind = kind
        self.vendor = vendor
        self.ident = ident
        self._topic = Topic.for_device(
            name=self.name,
            kind=self.kind,
            ident=self.ident,
            groups=[]
        )

    @property
    def topic(self) -> Topic:
        return self._topic

    def set_topic(self) -> str:
        "Creates a set-topic for the device"
        return self.topic.as_set()

    def get_topic(self) -> str:
        "Creates a set-topic for the device"
        return self.topic.as_get()
