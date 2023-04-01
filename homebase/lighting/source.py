"Abstract light and stuff."

from abc import ABC, abstractmethod
from typing import List, Optional

import common
from colour import Color
from comm import Payload
from enums import DeviceModel
from device import Addressable, Device
from lighting.config import Config, Override
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
    @abstractmethod
    def state(self) -> State:
        "The light state."

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
    def override_static(self, static: State):
        "Permanently overrides parent's static state."
        self._config.static = Override.perm(static)

    def inherit_static(self):
        "Inherit parent's static state."
        self._config.static = Override.none()

    def override_colorful(self, colorful: bool):
        "Permanently overrides parent's colorful-flag."
        self._config.colorful = Override.perm(colorful)

    def override_colorful_temporarily(self, colorful: bool):
        "Temporarily overrides parent's colorful-flag."
        self._config.colorful = Override.perm(colorful)

    def inherit_colorful(self):
        "Inherit parent's colorful-flag."
        self._config.colorful = Override.none()

    def override_dynamic(self, dynamic: bool):
        "Permanently overrides parent's dynamic-flag."
        self._config.dynamic = Override.perm(dynamic)

    def override_dynamic_temporarily(self, dynamic: bool):
        "Temporarily overrides parent's dynamic-flag."
        self._config.dynamic = Override.perm(dynamic)

    def inherit_dynamic(self):
        "Inherit parent's dynamic-flag."
        self._config.dynamic = Override.none()

    def adapt_brightness_mod(self, diff: float):
        "Permanently modifies the brightness."
        mod = self.__adapt_modifier(self._config.brightness_mod, diff)
        self._config.brightness_mod = Override.perm(mod)

    def adapt_brightness_mod_temporarily(self, diff: float):
        "Temporarily modifies the brightness."
        mod = self.__adapt_modifier(self._config.brightness_mod, diff)
        self._config.brightness_mod = Override.temp(mod)

    def set_brightness_mod_temporarily(self, val: float):
        "Temporarily modifies the brightness."
        self._config.brightness_mod = Override.temp(val)

    # def set_white_temp_mod(self, modifier: float):
    #     "Permanently modifies the white temperature."
    #     modifier = common.bounded(modifier, least=-1.0, greatest=+1.0)
    #     self._config.white_temp_mod = Override.perm(modifier)

    def adapt_color_offset(self, modifier: int):
        "Permanently offsets the color."
        mod = self._config.brightness_mod.value_or(0)
        modifier = int(common.bounded(float(mod), least=0.0, greatest=5.0))
        self._config.color_offset = Override.perm(modifier)

    def adapt_color_offset_temporarily(self, modifier: int):
        "Temporarily offsets the color."
        mod = self._config.brightness_mod.value_or(0)
        modifier = int(common.bounded(float(mod), least=0.0, greatest=5.0))
        self._config.color_offset = Override.temp(modifier)

    def __adapt_modifier(self, override: Override[float], diff: float) -> float:
        mod = override.value_or(0) + diff
        return common.bounded(mod, least=-1.0, greatest=+1.0)

    ################################################
    # FUNCTIONAL API
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

    @abstractmethod
    def turn_on(self, client: mqtt.Client):
        "turn all lights on"

    @abstractmethod
    def turn_off(self, client: mqtt.Client):
        "turn all lights off"

    @abstractmethod
    def toggle(self, client: mqtt.Client):
        "toggles all lights"

    @abstractmethod
    def shift_color_clockwise(self):
        "Shift color clockwise"

    @abstractmethod
    def shift_color_counter_clockwise(self):
        "Shift color counter clockwise"

    @abstractmethod
    def dim_up(self):
        "Increases brightness"

    @abstractmethod
    def dim_down(self):
        "Decreases brightness"

    @abstractmethod
    def set_brightness(self, brightness: float):
        """
            Updates internal state to claim the devices emits the given brightness.
        """

    @abstractmethod
    def set_white_temp(self, client: Optional[mqtt.Client], temp: float):
        """
            Updates internal state to claim the device emits the given white color temperature.
            Also physically realizes the state if a client is given.
        """

    @abstractmethod
    def set_color_temp(self, color: Color):
        """
            Updates internal state to claim the device emits the given color.
        """


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
        self._state = State()

    @property
    def state(self) -> State:
        return self._state

    @property
    def is_dimmable(self) -> bool:
        return self.model.is_dimmable

    @property
    def is_color(self) -> bool:
        return self.model.is_color

    ################################################
    # FUNCTIONAL API
    ################################################

    def update_virtual_state(self, state: State):
        "Updates the internal state without changing anything regarding the physical state."
        self._state = state

    def realize_state(self, client: mqtt.Client, state: State):
        self._set_toggled_on(None, state.toggled_on)
        self.set_brightness(state.brightness)
        self.set_white_temp(None, state.white_temp)
        self.set_color_temp(state.color)
        self._update_state(client)

    def start_dim_down(self, client: mqtt.Client):
        client.publish(self.set_topic(), Payload.start_dim(down=True))

    def start_dim_up(self, client: mqtt.Client):
        client.publish(self.set_topic(), Payload.start_dim(down=False))

    def stop_dim(self, client: mqtt.Client):
        client.publish(self.set_topic(), Payload.stop_dim())

    def turn_on(self, client: mqtt.Client):
        self._set_toggled_on(client, True)

    def turn_off(self, client: mqtt.Client):
        self._set_toggled_on(client, False)

    def toggle(self, client: mqtt.Client):
        self._set_toggled_on(client, not self.state.toggled_on)

    def shift_color_clockwise(self):
        self.state.color.hue += 0.2

    def shift_color_counter_clockwise(self):
        self.state.color.hue -= 0.2

    def dim_up(self):
        self.adapt_brightness_mod_temporarily(+0.2)

    def dim_down(self):
        self.adapt_brightness_mod_temporarily(-0.2)

    def set_brightness(self, brightness: float):
        desired = brightness = max(0, min(1, brightness))
        actual = self._state.brightness
        modifier = common.engineer_modifier(actual, desired)
        self.set_brightness_mod_temporarily(modifier)

    def set_white_temp(self, client: Optional[mqtt.Client], temp: float):
        self._state.white_temp = temp
        if client is not None:
            self._update_state(client)

    def set_color_temp(self, color: Color):
        self._state.color = color


    ################################################
    # FUNCTIONAL API
    ################################################

    def flatten_lights(self) -> List['Concrete']:
        return [self]

    ################################################
    # Internal Functions
    ################################################
    def _set_toggled_on(self, client: Optional[mqtt.Client], toggled_on: bool):
        """
            Updates internal state to claim the device is toggled on.
            Also physically realizes the state if a client is given.
        """
        self._state.toggled_on = toggled_on
        if client is not None:
            self._update_state(client)

    def _update_state(self, client: mqtt.Client):
        "Updates the physical state of the light depending on its virtual state."
        payload = self.state_change_payload()
        if payload is not None:
            client.publish(self.set_topic(), payload.finalize())

    def state_change_payload(self) -> Optional[Payload]:
        "Creates a payload to realize the current virtual state."
        payload = Payload().state(self.state.toggled_on)
        if self.is_dimmable:
            new_brightness = int(self.state.toggled_on) * self.state.brightness
            payload = payload.brightness(new_brightness)
        if self.is_color:
            new_white = int(self.state.toggled_on) * self.state.white_temp
            payload = payload.white_temp(new_white, vendor=self.vendor)
            payload = payload.color(self.state.color, self.vendor)
        return payload
