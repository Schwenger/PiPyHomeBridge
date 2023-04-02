"Abstract light and stuff."

from abc import ABC, abstractmethod
from typing import List, Optional
from copy import deepcopy

import common
from colormath.color_objects import HSVColor
from comm import Payload
from device import Addressable, Device
from enums import DeviceModel
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
    def is_white_spec(self) -> bool:
        "Can the light display white color?"

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
        self.accommodate_color(desired=desired.color, actual=actual.color)
        copy = deepcopy(self.config)
        self.accommodate_color(desired=desired.color, actual=actual.color)
        assert copy == self.config  # ToDo: Remove eventually.

    def accommodate_color(self, desired: HSVColor, actual: HSVColor):
        "Changes config to result in the desired color after refresh."
        common.Log.utl.debug("Actual: %s", actual)
        common.Log.utl.debug("Desired: %s", desired)
        hue_mod = common.engineer_modifier(actual.hsv_h, desired.hsv_h)  # ∈ [-1, +1]
        sat_mod = common.engineer_modifier(actual.hsv_s, desired.hsv_s)  # ∈ [-1, +1]
        lum_mod = common.engineer_modifier(actual.hsv_v, desired.hsv_v)  # ∈ [-1, +1]
        common.Log.utl.debug("Engineered hue modifier is %.2f.", hue_mod)
        common.Log.utl.debug("Engineered sat modifier is %.2f.", sat_mod)
        common.Log.utl.debug("Engineered lum modifier is %.2f.", lum_mod)
        self.config.hue.modify_temp(       0.0, lambda x: common.bounded(x + hue_mod))
        self.config.saturation.modify_temp(0.0, lambda x: common.bounded(x + sat_mod))
        self.config.lumin.modify_temp(     0.0, lambda x: common.bounded(x + lum_mod))
        common.Log.utl.debug("New modifier is %.2f.", self.config.hue.value)
        common.Log.utl.debug("New modifier is %.2f.", self.config.saturation.value)
        common.Log.utl.debug("New modifier is %.2f.", self.config.lumin.value)

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
        self.config.hue.modify_temp(0.0, lambda val: (val + 0.2) % 1)

    def shift_color_counter_clockwise(self):
        "Shift color counter clockwise"
        self.config.hue.modify_temp(0.0, lambda val: (val - 0.2) % 1)

    def dim_up(self):
        "Increases brightness"
        self.config.lumin.modify_temp(0.0, lambda val: common.bounded(val + 0.3))

    def dim_down(self):
        "Decreases brightness"
        self.config.lumin.modify_temp(0.0, lambda val: common.bounded(val - 0.3))

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
    def is_white_spec(self) -> bool:
        return self.model.is_white_spec

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
            new_brightness = int(state.toggled_on) * state.color.hsv_v
            payload = payload.brightness(new_brightness)
        if self.is_white_spec and not self.is_color:
            # ToDo
            pass
        if self.is_color:
            payload = payload.color(state.color, self.vendor)
        return payload
