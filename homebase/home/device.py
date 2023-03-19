"Definition of devices."

from abc import ABC, abstractmethod

from comm.topic import Topic
from enums import DeviceKind, DeviceModel, Vendor

TOPIC_BASE = "zigbee2mqtt"


class Addressable(ABC):
    "Marks an entity as addressable."

    def __init__(self):
        pass

    @property
    @abstractmethod
    def topic(self) -> Topic:
        "Returns the topic to address this entity"


class Device(Addressable, ABC):
    "Represents a generic device"

    def __init__(
        self,
        name: str,
        room: str,
        model: DeviceModel,
        ident: str,
    ):
        self.name = name
        self.room = room
        self.model = model
        self.ident = ident
        self._topic = Topic.for_device(
            name=self.name,
            kind=self.model.kind,
            ident=self.ident,
            groups=[]
        )

    @property
    def vendor(self) -> Vendor:
        "Specifies the vendor of the device, Ikea or Hue."
        return self.model.vendor

    @property
    def kind(self) -> DeviceKind:
        "Specifies the physical kind of the device."
        return self.model.kind

    @property
    def topic(self) -> Topic:
        return self._topic

    def set_topic(self) -> str:
        "Creates a set-topic for the device"
        return self.topic.as_set()

    def get_topic(self) -> str:
        "Creates a set-topic for the device"
        return self.topic.as_get()
