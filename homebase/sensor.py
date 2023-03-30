"An abstract base class for anything sensor-related."

from typing import Dict
from device import Device
from enums import DeviceModel, SensorQuantity


class Sensor(Device):
    "Represents a sensor."

    def __init__(
        self,
        name: str,
        room: str,
        model: DeviceModel,
        ident: str,
    ):
        super().__init__(
            name=name, room=room, model=model, ident=ident
        )
        self._state = {}

    @property
    def state(self) -> Dict[SensorQuantity, float]:
        "Returns a copy of the sensors current state."
        return self._state

    def update_state(self, key: SensorQuantity, value: float):
        "Updates the internal state."
        self._state[key] = value
