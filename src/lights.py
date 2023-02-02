"Handling lights in all shapes and forms."
from abc import ABC, abstractmethod
from paho.mqtt import client as mqtt
from colour import Color
from device import Device
import payload
from light_config import LightConfig
from log import trace, info

class Light(Device, ABC):
    "Abstract Light"

    def __init__(self, name: str, room: str, kind: str = "Light"):
        super().__init__(name=name, room=room, kind=kind)
        self.toggled_on: bool = False
        self.brightness: float = 0
        self.white_temp: float = 0
        self.color: Color = Color("White")

    def apply_config(self, client: mqtt.Client, cfg: LightConfig):
        "Applies the given LightConfig."
        trace(self.name, "apply_config")
        self.toggled_on = cfg.is_on
        self.set_brightness(client, cfg.brightness, update=False)
        self.set_white_temp(client, cfg.white_temp, update=False)
        self.set_color_temp(client, cfg.color_temp, update=False)
        self.update_state(client)

    def turn_physically_on(self, client: mqtt.Client):
        "Unconditionally turns the light on."
        trace(self.name, "turn_physically_on")
        self.toggled_on = True
        self.set_brightness(client, 1)
        self.update_state(client)

    def turn_physically_off(self, client: mqtt.Client):
        "Unconditionally turns the light off."
        trace(self.name, "turn_physically_off")
        self.toggled_on = False
        self.set_brightness(client, 0)
        self.update_state(client)

    def toggle(self, client: mqtt.Client):
        "Virtually toggles the light."
        trace(self.name, "toggle")
        self.toggled_on = not self.toggled_on
        self.update_state(client)

    def is_on(self) -> bool:
        """Indicates whether the abstract entity considers itself to be on.
        This can be the case even if the entity physically does not emit any light."""
        trace(self.name, "is_on")
        return self.toggled_on

    @abstractmethod
    def update_state(self, client: mqtt.Client):
        "Updates the physical state of the light depending on its virtual state."

    def set_brightness(self, client: mqtt.Client, brightness: float, update: bool = True):
        "Sets the brightness of the light source to the specified value if possible"
        trace(self.name, "set_brightness")
        info("Setting brightness to " + str(brightness))
        self.brightness = brightness
        if update:
            self.update_state(client)

    def set_color_temp(self, client: mqtt.Client, color: Color, update: bool = True):
        "Sets the color to the given color"
        trace(self.name, "set_color_temp")
        self.color = color
        if update:
            self.update_state(client)

    def set_white_temp(self, client: mqtt.Client, temp: float, update: bool = True):
        "Sets the color to the given white temperature"
        trace(self.name, "set_white_temp")
        self.white_temp = temp
        if update:
            self.update_state(client)

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

    def is_dimmable(self) -> bool:
        "Can the light be dimmed in any way?"
        return True

    def is_color(self) -> bool:
        "Determines if the light can display different colors"
        return False

    def update_state(self, client: mqtt.Client):
        trace(self.name, "update_state")
        client.publish(self.set_topic(), payload.brightness(self.brightness))
        if self.toggled_on:
            client.publish(self.set_topic(), payload.on)
        else:
            client.publish(self.set_topic(), payload.off)


class WhiteSpectrumLight(DimmableLight):
    "A light of varying brightness."

    def __init__(self, name: str, room: str, kind: str = "Light"):
        super().__init__(name=name, room=room, kind=kind)

    def is_dimmable(self) -> bool:
        "Can the light be dimmed in any way?"
        return True

    def is_color(self) -> bool:
        "Determines if the light can display different colors"
        return False

    def update_state(self, client: mqtt.Client):
        trace(self.name, "update_state")
        super().update_state(client)
        client.publish(self.set_topic(), payload.hue_color_temp(self.white_temp))

class ColorLight(DimmableLight):
    "A light of varying color"

    def __init__(self, name: str, room: str, kind: str = "Light"):
        super().__init__(name=name, room=room, kind=kind)

    def is_color(self) -> bool:
        "Determines if the light can display different colors"
        return True

    def update_state(self, client: mqtt.Client):
        trace(self.name, "update_state")
        super().update_state(client)
        client.publish(self.set_topic(), payload.color(self.color))

class SimpleLight(Light):
    "A simple on-off light"

    BRIGHTNESS_THRESHOLD = 0.33

    def __init__(self, name: str, room: str, kind="Light"):
        super().__init__(name=name, room=room, kind=kind)

    def is_dimmable(self) -> bool:
        "Can the light be dimmed in any way?"
        return False

    def is_color(self) -> bool:
        "Determines if the light can display different colors"
        return False

    def over_threshold(self) -> bool:
        "Returns true if the virtual brightness suggests this light should be on."
        return self.brightness > self.BRIGHTNESS_THRESHOLD

    def update_state(self, client: mqtt.Client):
        "Turns the light on or of depending on the virtual brightness and toggle state"
        if self.is_on() and self.over_threshold():
            client.publish(self.set_topic(), payload.on)
        else:
            client.publish(self.set_topic(), payload.off)


def create_simple(name: str, room: str, kind: str = "Light") -> SimpleLight:
    "Creates a simple on-off light"
    return SimpleLight(name=name, room=room, kind=kind)

def create_dimmable(name: str, room: str) -> DimmableLight:
    "Creates a dimmable light"
    return DimmableLight(name=name, room=room)

def create_white_spec(name: str, room: str) -> DimmableLight:
    "Creates a white spectrum light"
    return WhiteSpectrumLight(name=name, room=room)

def create_color(name: str, room: str) -> ColorLight:
    "Creates a color light"
    return ColorLight(name=name, room=room)
