"Handling lights in all shapes and forms."
from enum import Enum
from paho.mqtt import client as mqtt
from colour import Color
from device import Device
from payload import Payload
from light_config import LightConfig
from log import trace, info

class SimpleLightOnOff(Enum):
    "Represents the current physical and virtual on-off-state of the light."
    ON = 1
    OFF = 2
    ON_WITH_INSUFF_BRIGHT = 3
    OFF_WITH_INSUFF_BRIGHT = 4

class Light(Device):
    "Represents a light"

    def __init__(self, name: str, room: str, kind: str = "Light"):
        super().__init__(name=name, room=room, kind=kind)
        self.on_off = SimpleLightOnOff.OFF  # TODO: Retrieve from device

    ##### PUBLIC #####
    def turn_off(self, client: mqtt.Client):
        "Turns the light off."
        trace(name = self.name, fun = "turn off")
        self._turn_physically_off(client)
        self.on_off = SimpleLightOnOff.OFF

    def turn_on(self, client: mqtt.Client):
        "Turns the light on."
        trace(name = self.name, fun = "turn on")
        self._turn_physically_on(client)
        self.on_off = SimpleLightOnOff.ON

    def toggle(self, client: mqtt.Client):
        "Virtually toggles the light."
        trace(name = self.name, fun = "toggle")
        if self.on_off == SimpleLightOnOff.ON:
            self.turn_off(client)
        elif self.on_off == SimpleLightOnOff.OFF:
            self.turn_on(client)
        elif self.on_off == SimpleLightOnOff.ON_WITH_INSUFF_BRIGHT:
            self.on_off = SimpleLightOnOff.OFF_WITH_INSUFF_BRIGHT
        elif self.on_off == SimpleLightOnOff.OFF_WITH_INSUFF_BRIGHT:
            self.on_off = SimpleLightOnOff.ON_WITH_INSUFF_BRIGHT

    def apply_config(self, client: mqtt.Client, cfg: LightConfig):
        "Applies the given LightConfig."
        trace(name = self.name, fun = "apply config")
        self.set_brightness(client, cfg.brightness)
        self.set_white_temp(client, cfg.white_temp)
        self.set_color_temp(client, cfg.color_temp)

    def is_on(self) -> bool:
        "Indicates whether the light is virtually on."
        physically_on = self.on_off == SimpleLightOnOff.ON
        only_virtually_on = self.on_off == SimpleLightOnOff.ON_WITH_INSUFF_BRIGHT
        return physically_on or only_virtually_on

    ##### OVERRIDE #####

    def set_brightness(self, client: mqtt.Client, brightness: float):
        "Sets the brightness the specified value if possible."
        trace(name = self.name, fun = "set brightness")
        info("In set brightness of a simple light to: " + str(brightness))
        if brightness < 0.33:
            self.on_off = SimpleLightOnOff.ON_WITH_INSUFF_BRIGHT
            self._turn_physically_off(client)
        else:
            self.on_off = SimpleLightOnOff.ON
            self._turn_physically_on(client)

    def set_color_temp(self, _client: mqtt.Client, _color: Color):
        "Sets the color to the given hex string"
        trace(name = self.name, fun = "set color temp")

    def set_white_temp(self, _client: mqtt.Client, _temp: float):
        "Sets the color to the given hex string"
        trace(name = self.name, fun = "set white color temp")

    def is_dimmable(self) -> bool:
        "Can the light be dimmed in any way?"
        trace(name = self.name, fun = "is dimmable")
        return False

    ##### PRIVATE #####

    def _turn_physically_off(self, client: mqtt.Client):
        "Physically turns the light off; no more, no less."
        trace(name = self.name, fun = "turn physically off")
        client.publish(self.set_topic(), Payload.off)

    def _turn_physically_on(self, client: mqtt.Client):
        "Physically turns the light on; no more, no less."
        trace(name = self.name, fun = "turn physically on")
        client.publish(self.set_topic(), Payload.on)

    ##### STATIC #####

    @staticmethod
    def simple(name: str, room: str, kind: str = "Light") -> 'Light':
        "Creates a simple on-off light"
        return Light(name=name, room=room, kind=kind)

    @staticmethod
    def dimmable(name: str, room: str) -> 'Light':
        "Creates a dimmable light"
        return DimmableLight(name=name, room=room, kind="Light")

    @staticmethod
    def color(name: str, room: str) -> 'Light':
        "Creates a color light"
        return ColorLight(name=name, room=room, kind="Light")

class DimmableLight(Light):
    "Represents a dimmable light"

    def __init__(self, name: str, room: str, kind: str):
        super().__init__(name=name, room=room, kind=kind)

    def set_brightness(self, client: mqtt.Client, brightness: float):
        "Sets the scaled brightness if possible."
        trace(name = self.name, fun = "set brightness", cls = "Dimmable")
        info("In set brightness of a dimmable light to: " + str(brightness))
        client.publish(self.set_topic(), Payload.brightness(brightness))
        if brightness == 0:
            self.on_off = SimpleLightOnOff.OFF
        else:
            self.on_off = SimpleLightOnOff.ON

    def is_dimmable(self) -> bool:
        "Can the light be dimmed in any way?"
        trace(name = self.name, fun = "is_dimmable", cls = "Dimmable")
        return True

class WhiteSpectrumLight(DimmableLight):
    "Represents a white spectrum light"

    def __init__(self, name: str, room: str, kind: str):
        super().__init__(name=name, room=room, kind=kind)

    def set_white_temp(self, client: mqtt.Client, temp: float):
        "Sets the white color temperature."
        trace(name = self.name, fun = "set_white_temp", cls = "WhiteSpectrum")
        client.publish(self.set_topic(), Payload.ikea_color_temp(temp))

class ColorLight(DimmableLight):
    "Represents a color light"

    def __init__(self, name: str, room: str, kind: str):
        super().__init__(name=name, room=room, kind=kind)

    def set_color_temp(self, client: mqtt.Client, color: Color):
        "Sets the color to the given hex string"
        trace(name = self.name, fun = "set_color_temp", cls = "ColorLight")
        client.publish(self.set_topic(), Payload.color(color))
