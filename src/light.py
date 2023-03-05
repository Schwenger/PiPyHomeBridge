"Handling lights in all shapes and forms."
import math
from abc import ABC, abstractmethod
from typing import Optional, List
from paho.mqtt import client as mqtt
from colour import Color
from device import Device, DeviceKind, Vendor, Addressable
import payload

class LightState:
    "Represents the state of a light."
    def __init__(
        self,
        toggled_on: bool = False,
        brightness: float = 0,
        white_temp: float = 0,
        color: Color = Color("White")
    ):
        self.toggled_on: bool = toggled_on
        self.brightness: float = brightness
        self.white_temp: float = white_temp
        self.color: Color = color

    def with_color(self, color: Color):
        "Reduces or increases brightness  and turns color (counter-)clockwise."
        self.color = color

    def with_brightness(self, brightness: float):
        "Sets the brightness to the specified value"
        self.brightness = brightness
        self.white_temp = self.brightness

    def purge_color(self):
        "Returns an identical LightConfig just with a white color."
        self.color = Color("White")

    def purge_dimming(self):
        "Returns an identical LightConfig just with a max brightness."
        self.brightness = 1
        self.white_temp = 1

    @staticmethod
    def average(states: List['LightState']) -> 'LightState':
        "Returns a light state that roughly resembles the average light state of the given ones."
        ons = 0
        brightness = 0.0
        white_temp = 0.0
        red = 0.0
        green = 0.0
        blue = 0.0
        for state in states:
            ons += int(state.toggled_on)
            brightness += state.brightness
            white_temp += state.white_temp
            red += state.color.get_red()**2
            green += state.color.get_green()**2
            blue += state.color.get_blue()**2
        # pylint: disable=invalid-name
        n = len(states)
        red = math.sqrt(red/n)
        green = math.sqrt(green/n)
        blue = math.sqrt(blue/n)
        return LightState(
            toggled_on = ons / n >= 0.5,
            brightness=brightness/n,
            white_temp=white_temp/n,
            color=Color(rgb=(red, green, blue))
        )

class AbstractLight(Addressable, ABC):
    """
        Carries the informational and function API of light sources.
    """

    @property
    @abstractmethod
    def state(self) -> LightState:
        "The light state."

    ################################################
    ############## INFORMATIONAL API ###############
    ################################################
    @abstractmethod
    def is_dimmable(self) -> bool:
        "Can the light be dimmed in any way?"

    @abstractmethod
    def is_color(self) -> bool:
        "Determines if the light can display different colors"

    ################################################
    ##### FUNCTIONAL API
    ################################################

    @abstractmethod
    def realize_state(self, client: mqtt.Client, state: LightState):
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

class ConcreteLight(Device, ABC):
    """
        Represents a concrete, physical light source, e.g. a light source
        or an outlet controlling naught but a light.
        Translates virtual commands like 'set the brightness to 50' into
        physical commands sent over the mqtt bridge.
    """

    def __init__(self,
        name: str,
        room: str,
        ident: str,
        kind: DeviceKind = DeviceKind.Light,
        vendor: Vendor = Vendor.Ikea,
    ):
        super().__init__(name=name, room=room, kind=kind, vendor=vendor, ident=ident)
        self.__state = LightState()

    @property
    def _state(self) -> LightState:
        "The virtual state of the light"
        return self.__state

    @abstractmethod
    def update_state(self, client: mqtt.Client):
        "Updates the physical state of the light depending on its virtual state."

    def set_toggled_on(self, client: Optional[mqtt.Client], toggled_on: bool):
        """
            Updates internal state to claim the device is toggled on.
            Also physically realizes the state if a client is given.
        """
        self._state.toggled_on = toggled_on
        if client is not None:
            self.update_state(client)

    def set_brightness(self, client: Optional[mqtt.Client], brightness: float):
        """
            Updates internal state to claim the devices emits the given brightness.
            Also physically realizes the state if a client is given.
        """
        self._state.brightness = max(0, min(1, brightness))
        if client is not None:
            self.update_state(client)

    def set_white_temp(self, client: Optional[mqtt.Client], temp: float):
        """
            Updates internal state to claim the device emits the given white color temperature.
            Also physically realizes the state if a client is given.
        """
        self._state.white_temp = temp
        if client is not None:
            self.update_state(client)

    def set_color_temp(self, client: Optional[mqtt.Client], color: Color):
        """
            Updates internal state to claim the device emits the given color.
            Also physically realizes the state if a client is given.
        """
        self._state.color = color
        if client is not None:
            self.update_state(client)

    def _realize_state(self, client: mqtt.Client, state: LightState):
        self.set_toggled_on(None, state.toggled_on)
        self.set_brightness(None, state.brightness)
        self.set_white_temp(None, state.white_temp)
        self.set_color_temp(None, state.color)
        self.update_state(client)

    #######################################
    ##### QUERY
    #######################################
    def query_state(self, client: mqtt.Client):
        """
        Queries a message containing the current brightness of the light.
        Does NOT update anything in the light.
        """
        client.publish(self.get_topic(), payload.state(None))

    def query_brightness(self, client: mqtt.Client):
        """
        Queries a message containing the current brightness of the light.
        Does NOT update anything in the light.
        """
        client.publish(self.get_topic(), payload.brightness(None))

class Light(AbstractLight, ConcreteLight, ABC):
    """
        Translates abstract commands like 'Dim the light!' into a virtual
        state like 'brightness: 50'.
    """

    @property
    def state(self) -> LightState:
        "The virtual state of the light"
        return self._state

    def realize_state(self, client: mqtt.Client, state: LightState):
        self._realize_state(client, state)

    ################################################
    ##### FUNCTIONAL API
    ################################################

    def turn_on(self, client: mqtt.Client):
        self.set_toggled_on(client, True)

    def turn_off(self, client: mqtt.Client):
        self.set_toggled_on(client, False)

    def toggle(self, client: mqtt.Client):
        self.set_toggled_on(client, not self.state.toggled_on)

    def shift_color_clockwise(self, client: mqtt.Client):
        self.state.color.hue += 0.2

    def shift_color_counter_clockwise(self, client: mqtt.Client):
        self.state.color.hue -= 0.2

    def dim_up(self, client: mqtt.Client):
        self.set_brightness(client, self.state.brightness + 0.2)

    def dim_down(self, client: mqtt.Client):
        self.set_brightness(client, self.state.brightness - 0.2)
