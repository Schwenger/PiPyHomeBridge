"Abstract light and stuff."

from abc import ABC, abstractmethod
from typing import Optional

from colour import Color
from home.device import Addressable
from lighting.state import State
from paho.mqtt import client as mqtt


class Abstract(Addressable, ABC):
    """
        Carries the informational and function API of light sources.
    """

    @property
    @abstractmethod
    def state(self) -> State:
        "The light state."

    ################################################
    # INFORMATIONAL API
    ################################################
    @abstractmethod
    def is_dimmable(self) -> bool:
        "Can the light be dimmed in any way?"

    @abstractmethod
    def is_color(self) -> bool:
        "Determines if the light can display different colors"

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
    def shift_color_clockwise(self, client: mqtt.Client):
        "Shift color clockwise"

    @abstractmethod
    def shift_color_counter_clockwise(self, client: mqtt.Client):
        "Shift color counter clockwise"

    @abstractmethod
    def dim_up(self, client: mqtt.Client):
        "Increases brightness"

    @abstractmethod
    def dim_down(self, client: mqtt.Client):
        "Decreases brightness"

    @abstractmethod
    def set_brightness(self, client: Optional[mqtt.Client], brightness: float):
        """
            Updates internal state to claim the devices emits the given brightness.
            Also physically realizes the state if a client is given.
        """

    @abstractmethod
    def set_white_temp(self, client: Optional[mqtt.Client], temp: float):
        """
            Updates internal state to claim the device emits the given white color temperature.
            Also physically realizes the state if a client is given.
        """

    @abstractmethod
    def set_color_temp(self, client: Optional[mqtt.Client], color: Color):
        """
            Updates internal state to claim the device emits the given color.
            Also physically realizes the state if a client is given.
        """
