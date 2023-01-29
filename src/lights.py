"Handling lights in all shapes and forms."
from abc import ABC, abstractmethod
from paho.mqtt import client as mqtt
from colour import Color
from device import Device
from payload import Payload
from light_config import LightConfig

class LightInternalState:
    "The state of an abstract light source"
    def __init__(self, is_on: bool, brightness: float, color: Color, time):
        self.is_on = is_on
        self.brightness = brightness
        self.color = color
        self.time = time

class Light(Device, ABC):
    "Abstract Light"

    def __init__(self, name: str, room: str, kind: str = "Light"):
        super(Light, self).__init__(name=name, room=room, kind=kind)
        # state = self.retrieve_state(None) Todo
        # self.update_internal_state(state)

    def retrieve_state(self, _client: mqtt.Client) -> LightInternalState:
        "Retrieves the internal state from the device itself"
        return None

    def apply_config(self, client: mqtt.Client, cfg: LightConfig):
        "Applies the given LightConfig."
        self.set_brightness(client, cfg.brightness)
        self.set_white_temp(client, cfg.white_temp)
        self.set_color_temp(client, cfg.color_temp)

    @abstractmethod
    def update_internal_state(self, state: LightInternalState):
        "Updates the internal state based on the information gained"

    @abstractmethod
    def turn_physically_on(self, client: mqtt.Client):
        "Unconditionally turns the light on."

    @abstractmethod
    def turn_physically_off(self, client: mqtt.Client):
        "Unconditionally turns the light on."

    @abstractmethod
    def toggle(self, client: mqtt.Client):
        "Virtually toggles the light."

    @abstractmethod
    def is_on(self) -> bool:
        """Indicates whether the abstract entity considers itself to be on.
        This can be the case even if the entity physically does not emit any light."""

    @abstractmethod
    def set_brightness(self, client: mqtt.Client, brightness: float):
        "Sets the brightness of the light source to the specified value if possible"

    @abstractmethod
    def set_color_temp(self, _client: mqtt.Client, _color: Color):
        "Sets the color to the given color"

    @abstractmethod
    def set_white_temp(self, _client: mqtt.Client, _temp: float):
        "Sets the color to the given white temperature"

    @abstractmethod
    def is_dimmable(self) -> bool:
        "Can the light be dimmed in any way?"

    @abstractmethod
    def is_color(self) -> bool:
        "Determines if the light can display different colors"

class DimmableLight(Light):
    "A light of varying brightness."

    def __init__(self, name: str, room: str, kind: str = "Light"):
        super().__init__(name=name, room=room, kind=kind)
        self.brightness = 0

    def update_internal_state(self, state: LightInternalState):
        "Updates the internal state based on the information gained"
        if state is not None:
            self.brightness = state.brightness

    def turn_physically_on(self, client: mqtt.Client):
        "Unconditionally turns the light on."
        self.set_brightness(client, 1)

    def turn_physically_off(self, client: mqtt.Client):
        "Unconditionally turns the light on."
        self.set_brightness(client, 0)

    def toggle(self, client: mqtt.Client):
        "Virtually toggles the light."
        client.publish(self.set_topic(), Payload.toggle)

    def is_on(self) -> bool:
        """Indicates whether the abstract entity considers itself to be on.
        This can be the case even if the entity physically does not emit any light."""
        return self.brightness > 0

    def set_brightness(self, client: mqtt.Client, brightness: float):
        "Sets the brightness of the light source to the specified value if possible"
        client.publish(self.set_topic(), Payload.brightness(brightness))
        self.brightness = brightness

    def set_white_temp(self, _client: mqtt.Client, _temp: float):
        "Sets the color to the given white temperature"

    def set_color_temp(self, _client: mqtt.Client, _color: Color):
        "Sets the color to the given color"

    def is_dimmable(self) -> bool:
        "Can the light be dimmed in any way?"
        return True

    def is_color(self) -> bool:
        "Determines if the light can display different colors"
        return False

class ColorLight(DimmableLight):
    "A light of varying color"

    def __init__(self, name: str, room: str, kind: str = "Light"):
        super().__init__(name=name, room=room, kind=kind)
        self.brightness = 0
        self.color_temp = Color("White")

    def update_internal_state(self, state: LightInternalState):
        "Updates the internal state based on the information gained"
        super().update_internal_state(state)
        if state is not None:
            self.color_temp = state.color

    def set_color_temp(self, client: mqtt.Client, color: Color):
        "Sets the color to the given color"
        client.publish(self.set_topic(), Payload.color(color))
        self.color_temp = color

    def is_color(self) -> bool:
        "Determines if the light can display different colors"
        return True

class SimpleLight(Light):
    "A simple on-off light"

    BRIGHTNESS_THRESHOLD = 0.33

    def __init__(self, name: str, room: str, kind="Light"):
        super().__init__(name=name, room=room, kind=kind)
        self.virtual_brightness = 0

    def update_internal_state(self, state: LightInternalState):
        "Updates the internal state based on the information gained"
        if state is not None:
            if state.is_on:
                self.virtual_brightness = 1
            else:
                self.virtual_brightness = 0

    def turn_physically_on(self, client: mqtt.Client):
        "Unconditionally turns the light on."
        client.publish(self.set_topic(), Payload.on)
        self.virtual_brightness = 1

    def turn_physically_off(self, client: mqtt.Client):
        "Unconditionally turns the light on."
        client.publish(self.set_topic(), Payload.off)
        self.virtual_brightness = 0

    def toggle(self, client: mqtt.Client):
        "Virtually toggles the light."
        client.publish(self.set_topic(), Payload.toggle)
        self.virtual_brightness = (self.virtual_brightness + 1) % 2

    def is_on(self) -> bool:
        """Indicates whether the abstract entity considers itself to be on.
        This can be the case even if the entity physically does not emit any light."""
        return self.virtual_brightness > self.BRIGHTNESS_THRESHOLD

    def set_brightness(self, client: mqtt.Client, brightness: float):
        "Sets the brightness of the light source to the specified value if possible"
        if brightness > self.BRIGHTNESS_THRESHOLD and not self.is_on():
            self.turn_physically_on(client)
        if brightness <= self.BRIGHTNESS_THRESHOLD and self.is_on():
            self.turn_physically_off(client)
        self.virtual_brightness = brightness

    def set_white_temp(self, _client: mqtt.Client, _temp: float):
        "Sets the color to the given white temperature"

    def set_color_temp(self, _client: mqtt.Client, _color: Color):
        "Sets the color to the given color"

    def is_dimmable(self) -> bool:
        "Can the light be dimmed in any way?"
        return False

    def is_color(self) -> bool:
        "Determines if the light can display different colors"
        return False


def create_simple(name: str, room: str, kind: str = "Light") -> SimpleLight:
    "Creates a simple on-off light"
    return SimpleLight(name=name, room=room, kind=kind)

def create_dimmable(name: str, room: str) -> DimmableLight:
    "Creates a dimmable light"
    return DimmableLight(name=name, room=room)

def create_color(name: str, room: str) -> ColorLight:
    "Creates a color light"
    return ColorLight(name=name, room=room)