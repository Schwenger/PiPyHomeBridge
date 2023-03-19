"A concrete light, i.e. a physical device that represents a light."

from typing import Optional

from colour import Color
from comm.payload import Payload
from enums import DeviceModel
from home.device import Device
from lighting.abstract import Abstract
from lighting.state import State
from paho.mqtt import client as mqtt


class Concrete(Abstract, Device):
    """
        Represents a concrete, physical light source, e.g. a light source
        or an outlet controlling naught but a light.
        Translates virtual commands like 'set the brightness to 50' into
        physical commands sent over the mqtt bridge.
    """

    def __init__(
        self,
        name: str,
        room: str,
        model: DeviceModel,
        ident: str,
    ):
        Abstract.__init__(self, full_config=None, relative_config=None)
        Device.__init__(self, name=name, room=room, model=model, ident=ident)
        self._state = State()

    @property
    def state(self) -> State:
        return self._state

    ################################################
    # INFORMATIONAL API
    ################################################
    # Passed on:
    # def is_dimmable(self) -> bool:
    #     pass

    # def is_color(self) -> bool:
    #     pass

    ################################################
    # FUNCTIONAL API
    ################################################

    def realize_state(self, client: mqtt.Client, state: State):
        self._set_toggled_on(None, state.toggled_on)
        self.set_brightness(None, state.brightness)
        self.set_white_temp(None, state.white_temp)
        self.set_color_temp(None, state.color)
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

    def shift_color_clockwise(self, client: mqtt.Client):
        self.state.color.hue += 0.2
        self.set_color_temp(client, self.state.color)

    def shift_color_counter_clockwise(self, client: mqtt.Client):
        self.state.color.hue -= 0.2
        self.set_color_temp(client, self.state.color)

    def dim_up(self, client: mqtt.Client):
        self.set_brightness(client, self.state.brightness + 0.2)

    def dim_down(self, client: mqtt.Client):
        self.set_brightness(client, self.state.brightness - 0.2)

    def set_brightness(self, client: Optional[mqtt.Client], brightness: float):
        self._state.brightness = max(0, min(1, brightness))
        if client is not None:
            self._update_state(client)

    def set_white_temp(self, client: Optional[mqtt.Client], temp: float):
        self._state.white_temp = temp
        if client is not None:
            self._update_state(client)

    def set_color_temp(self, client: Optional[mqtt.Client], color: Color):
        self._state.color = color
        if client is not None:
            self._update_state(client)

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
        if self.is_dimmable():
            new_brightness = int(self.state.toggled_on) * self.state.brightness
            payload = payload.brightness(new_brightness)
        if self.is_color():
            new_white = int(self.state.toggled_on) * self.state.white_temp
            payload = payload.white_temp(new_white, vendor=self.vendor)
            payload = payload.color(self.state.color, self.vendor)
        return payload
