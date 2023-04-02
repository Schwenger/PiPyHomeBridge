"Abstract light and stuff."

from abc import ABC, abstractmethod
from typing import List, Optional

import common
from comm import Payload
from enums import DeviceModel
from device import Addressable, Device
from lighting.config import Config
from lighting.state import State
from paho.mqtt import client as mqtt


class Collection:
    "Indicates a collection of light sources."
    @abstractmethod
    def flatten_lights(self) -> List['Concrete']:
        "Returns all lights in the collection"


class Abstract(Addressable, ABC, Collection):
    """
        Carries the informational and function API of light sources.
    """

    def __init__(
        self,
        config: Config,
    ):
        self._config = config

    ################################################
    # PROPERTIES
    ################################################

    @property
    def config(self) -> Config:
        "Returns the light's current configuration."
        return self._config

    @property
    @abstractmethod
    def is_dimmable(self) -> bool:
        "Can the light be dimmed in any way?"

    @property
    @abstractmethod
    def is_color(self) -> bool:
        "Determines if the light can display different colors"

    ################################################
    # CONFIGURATIVE API
    ################################################
    def set_dynamic(self, dynamic: bool):
        "En- or disables dynamic dimming."
        self.config.dynamic.set_temp(dynamic)

    def set_colorful(self, colorful: bool):
        "En- or disables colorful mode."
        self.config.colorful.set_temp(colorful)

    ################################################
    # FUNCTIONAL API -- Passed on
    ################################################

    @abstractmethod
    def realize_state(self, client: mqtt.Client, state: State):
        "Realizes the given state."

    @abstractmethod
    def start_dim_down(self, client: mqtt.Client):
        "Starts gradually reducing the brightness."

    @abstractmethod
    def start_dim_up(self, client: mqtt.Client):
        "Starts gradually increasing the brightness."

    @abstractmethod
    def stop_dim(self, client: mqtt.Client):
        "Stops gradual change of brightness."

    ################################################
    # FUNCTIONAL API -- Implementations
    ################################################

    def accommodate_state(self, desired: State, actual: State):
        "Updates the internal config to result in the given physical state when refreshed."
        self.accommodate_brightness(desired=desired.brightness, actual=actual.brightness)

    def accommodate_brightness(self, desired: float, actual: float):
        "Changes config to result in the desired brightness after refresh."
        common.Log.utl.debug("Engineering modifier; actual: %.4f, desired: %.4f", actual, desired)
        modifier = common.engineer_modifier(actual, desired)
        common.Log.utl.debug("Engineered modifier is %.2f.", modifier)
        self.config.brightness_mod.modify_temp(0.0, lambda x: x + modifier)
        common.Log.utl.debug("New modifier is %.2f.", self.config.brightness_mod.value)

    def turn_on(self):
        "Turn all lights on"
        self.config.toggled_on.set_temp(True)

    def turn_off(self):
        "Turn all lights off"
        self.config.toggled_on.set_temp(False)

    def toggle(self):
        "Toggles all lights"
        old = self.config.toggled_on.value_or(False)
        self.config.toggled_on.set_temp(not old)

    def shift_color_clockwise(self):
        "Shift color clockwise"
        self.config.color_offset.modify_temp(0, lambda val: (val + 1) % 5)

    def shift_color_counter_clockwise(self):
        "Shift color counter clockwise"
        self.config.color_offset.modify_temp(0, lambda val: (val - 1) % 5)

    def dim_up(self):
        "Increases brightness"
        self.config.brightness_mod.modify_temp(0, lambda v: common.bounded(v + 0.3))

    def dim_down(self):
        "Decreases brightness"
        self.config.brightness_mod.modify_temp(0, lambda v: common.bounded(v - 0.3))

class Concrete(Abstract, Device):
    """
        Represents a concrete, physical light source, e.g. a light source
        or an outlet controlling naught but a light.
        Translates virtual commands like 'set the brightness to 50' into
        physical commands sent over the mqtt bridge.
    """

    def __init__(
        self,
        name:   str,
        room:   str,
        icon:   str,
        model:  DeviceModel,
        ident:  str,
        config: Config,
    ):
        Abstract.__init__(self, config=config)
        Device.__init__(self, name=name, room=room, icon=icon, model=model, ident=ident)

    @property
    def is_dimmable(self) -> bool:
        return self.model.is_dimmable

    @property
    def is_color(self) -> bool:
        return self.model.is_color

    ################################################
    # FUNCTIONAL API
    ################################################

    def realize_state(self, client: mqtt.Client, state: State):
        payload = self._state_realization_payload(state=state)
        if payload is not None:
            client.publish(self.set_topic(), payload.finalize())

    def start_dim_down(self, client: mqtt.Client):
        client.publish(self.set_topic(), Payload.start_dim(down=True))

    def start_dim_up(self, client: mqtt.Client):
        client.publish(self.set_topic(), Payload.start_dim(down=False))

    def stop_dim(self, client: mqtt.Client):
        client.publish(self.set_topic(), Payload.stop_dim())

    ################################################
    # Collection API
    ################################################

    def flatten_lights(self) -> List['Concrete']:
        return [self]

    ################################################
    # Internal Functions
    ################################################

    def _state_realization_payload(self, state: State) -> Optional[Payload]:
        "Creates a payload to realize the given state."
        payload = Payload().state(state.toggled_on)
        if self.is_dimmable:
            new_brightness = int(state.toggled_on) * state.brightness
            payload = payload.brightness(new_brightness)
        if self.is_color:
            new_white = int(state.toggled_on) * state.white_temp
            payload = payload.white_temp(new_white, vendor=self.vendor)
            payload = payload.color(state.color, self.vendor)
        return payload
