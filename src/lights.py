"Handling lights in all shapes and forms."
from abc import ABC, abstractmethod
import threading
import time
from typing import Optional
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
        self._toggled_on: bool = False
        self._brightness: float = 0
        self._white_temp: float = 0
        self._last_cfg: Optional[LightConfig] = None
        self._color: Color = Color("White")

    @abstractmethod
    def is_dimmable(self) -> bool:
        "Can the light be dimmed in any way?"

    @abstractmethod
    def is_color(self) -> bool:
        "Determines if the light can display different colors"

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
    def _update_state(self, client: mqtt.Client):
        "Updates the physical state of the light depending on its virtual state."

    def consume_message(self, client: mqtt.Client, data):
        if "state" in data:
            new_state = payload.transform_state(data["state"])
            self._toggled_on = new_state
        if "brightness" in data:
            brightness = payload.transform_brightness(data["brightness"])
            self._set_brightness(client, brightness, update=False)
        if "color_temp" in data:
            white = payload.transform_white_temp(data["color_temp"], "hue")
            self._set_white_temp(client, white, update=False)
        # if "color" in data:
            # color = payload.transform_color(
            #     x=data["color"]["x"],
            #     y=data["color"]["y"],
            #     Y=data["brightness"]
            # )
            # self.set_color_temp(client, color, update=False)

    def is_on(self) -> bool:
        """Indicates whether the abstract entity considers itself to be on.
        This can be the case even if the entity physically does not emit any light."""
        trace(self.name, "is_on")
        return self._toggled_on

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

    def apply_config(self, client: mqtt.Client, cfg: LightConfig):
        "Applies the given LightConfig."
        trace(self.name, "apply_config")
        self._last_cfg = self._compile_cfg()
        self._set_brightness(client, cfg.brightness, update=False)
        self._set_white_temp(client, cfg.white_temp, update=False)
        self._set_color_temp(client, cfg.color, update=False)
        self._toggled_on = cfg.is_on
        self._update_state(client)

    def _compile_cfg(self) -> LightConfig:
        return LightConfig(self._brightness, self._white_temp, self._color)

    def _turn_on_gently(self, client: mqtt.Client):
        self._toggled_on = True
        self._set_brightness(client, 0.01, update=False)
        self._set_white_temp(client, 0.01, update=False)
        self._update_state(client)

    def _turn_off(self, client: mqtt.Client):
        self._toggled_on = False
        self._set_brightness(client, 0)
        self._update_state(client)

    def _set_brightness(self, client: mqtt.Client, brightness: float, update: bool = True):
        "Sets the brightness of the light source to the specified value if possible"
        trace(self.name, "set_brightness")
        info("Setting brightness to " + str(brightness))
        self._brightness = brightness
        if update:
            self._update_state(client)

    def _set_white_temp(self, client: mqtt.Client, temp: float, update: bool = True):
        "Sets the color to the given white temperature"
        trace(self.name, "set_white_temp")
        self._white_temp = temp
        if update:
            self._update_state(client)

    def _set_color_temp(self, client: mqtt.Client, color: Color, update: bool = True):
        "Sets the color to the given color"
        trace(self.name, "set_color_temp")
        self._color = color
        if update:
            self._update_state(client)

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

    def start_dim_down(self, client: mqtt.Client):
        "Starts gradually reducing the brightness."
        client.publish(self.set_topic(), payload.start_dim_down())

    def start_dim_up(self, client: mqtt.Client):
        "Starts gradually reducing the brightness."
        client.publish(self.set_topic(), payload.start_dim_up())

    def stop_dim(self, client: mqtt.Client):
        "Starts gradually reducing the brightness."
        client.publish(self.set_topic(), payload.stop_dim())

    def _update_state(self, client: mqtt.Client):
        trace(self.name, "update_state")
        if self._toggled_on:
            client.publish(self.set_topic(), payload.on)
        else:
            client.publish(self.set_topic(), payload.off)
        client.publish(self.set_topic(), payload.brightness(self._brightness))


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

    def _update_state(self, client: mqtt.Client):
        trace(self.name, "update_state")
        super()._update_state(client)
        client.publish(self.set_topic(), payload.hue_color_temp(self._white_temp))

class ColorLight(DimmableLight):
    "A light of varying color"

    def __init__(self, name: str, room: str, kind: str = "Light"):
        super().__init__(name=name, room=room, kind=kind)

    def is_color(self) -> bool:
        "Determines if the light can display different colors"
        return True

    def _update_state(self, client: mqtt.Client):
        trace(self.name, "update_state")
        super()._update_state(client)
        client.publish(self.set_topic(), payload.color(self._color))

class SimpleLight(Light):
    "A simple on-off light"

    BRIGHTNESS_THRESHOLD = 0.33

    def __init__(self, name: str, room: str, kind="Light"):
        super().__init__(name=name, room=room, kind=kind)
        self.__lock = threading.Lock()
        self.__dimming = False

    def consume_message(self, client: mqtt.Client, data):
        # Physical state is kinda irrelevant for simple lights because it
        # might contradict our virtual state and offers no additional information.
        pass

    def _set_brightness(self, client: mqtt.Client, brightness: float, update: bool = True):
        "Sets the brightness of the light source to the specified value if possible"
        with self.__lock:
            super()._set_brightness(client, brightness, update)

    def is_dimmable(self) -> bool:
        "Can the light be dimmed in any way?"
        return False

    def is_color(self) -> bool:
        "Determines if the light can display different colors"
        return False

    def pseudo_dim(self, client: mqtt.Client, factor: int):
        "Quasi-dims the light discretely."
        return # Check back later.
        # while self.__dimming:
        #     with self.__lock:
        #         new_brightness = self._brightness + factor*payload.DEFAULT_DIMMING_SPEED
        #         super()._set_brightness(client, new_brightness, update=True)
        #     time.sleep(1)

    def start_dim_down(self, client: mqtt.Client):
        "Starts gradually reducing the brightness."
        threading.Thread(target=self.pseudo_dim, args=(client, -1)).start()
        self.__dimming = True

    def start_dim_up(self, client: mqtt.Client):
        "Starts gradually reducing the brightness."
        threading.Thread(target=self.pseudo_dim, args=(client, +1)).start()
        self.__dimming = True

    def stop_dim(self, client: mqtt.Client):
        "Starts gradually reducing the brightness."
        self.__dimming = False

    def over_threshold(self) -> bool:
        "Returns true if the virtual brightness suggests this light should be on."
        return self._brightness > self.BRIGHTNESS_THRESHOLD

    def _update_state(self, client: mqtt.Client):
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
