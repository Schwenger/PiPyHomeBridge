"Different types of light sources."

import time
from typing import Optional
import threading
from paho.mqtt import client as mqtt
from light import Light
import payload

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

    def update_state(self, client: mqtt.Client):
        if self.state.toggled_on:
            client.publish(self.set_topic(), payload.on)
        else:
            client.publish(self.set_topic(), payload.off)
        new_brightness = int(self.state.toggled_on) * self.state.brightness
        client.publish(self.set_topic(), payload.brightness(new_brightness))


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
        super().update_state(client)
        client.publish(self.set_topic(), payload.hue_color_temp(self.state.white_temp))

class ColorLight(DimmableLight):
    "A light of varying color"

    def __init__(self, name: str, room: str, kind: str = "Light"):
        super().__init__(name=name, room=room, kind=kind)

    def is_color(self) -> bool:
        "Determines if the light can display different colors"
        return True

    def update_state(self, client: mqtt.Client):
        super().update_state(client)
        client.publish(self.set_topic(), payload.color(self.state.color))

class SimpleLight(Light):
    "A simple on-off light"

    BRIGHTNESS_THRESHOLD = 0.33
    DIMMING_SPEED = 0.2

    def __init__(self, name: str, room: str, kind="Light"):
        super().__init__(name=name, room=room, kind=kind)
        self.__lock = threading.Lock()  # protects virtual brightness
        self.__dimming = False

    def set_brightness(self, client: Optional[mqtt.Client], brightness: float):
        "Sets the brightness of the light source to the specified value if possible"
        with self.__lock:
            super().set_brightness(client, brightness)

    def is_dimmable(self) -> bool:
        "Can the light be dimmed in any way?"
        return False

    def is_color(self) -> bool:
        "Determines if the light can display different colors"
        return False

    def pseudo_dim(self, client: mqtt.Client, factor: int):
        "Quasi-dims the light discretely."
        speed = 0.2
        while self.__dimming:
            with self.__lock:
                new_brightness = self.state.brightness + factor*speed*self.DIMMING_SPEED
                super().set_brightness(client, new_brightness)
            time.sleep(speed)

    def start_dim_down(self, client: mqtt.Client):
        "Starts gradually reducing the brightness."
        self.__dimming = True
        threading.Thread(target=self.pseudo_dim, args=(client, -1)).start()

    def start_dim_up(self, client: mqtt.Client):
        "Starts gradually reducing the brightness."
        self.__dimming = True
        threading.Thread(target=self.pseudo_dim, args=(client, +1)).start()

    def stop_dim(self, client: mqtt.Client):
        "Starts gradually reducing the brightness."
        self.__dimming = False

    def over_threshold(self) -> bool:
        "Returns true if the virtual brightness suggests this light should be on."
        return self.state.brightness > self.BRIGHTNESS_THRESHOLD

    def update_state(self, client: mqtt.Client):
        if self.state.toggled_on and self.over_threshold():
            client.publish(self.set_topic(), payload.on)
        else:
            client.publish(self.set_topic(), payload.off)

#######################################
### LIGHT CREATION
#######################################

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
