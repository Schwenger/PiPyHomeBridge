"Different types of light sources."

import time
from typing import Optional
import threading
from colour import Color
from paho.mqtt import client as mqtt
from light import Light, ConcreteLight
import payload
from device import DeviceKind, Vendor

class SimpleLight(Light):
    "A simple on-off light"

    BRIGHTNESS_THRESHOLD = 0.33
    DIMMING_SPEED = 0.2

    def __init__(self,
        name: str,
        room: str,
        vendor: Vendor,
        ident: str,
        kind: DeviceKind = DeviceKind.Light
    ):
        super().__init__(name=name, room=room, kind=kind, vendor=vendor, ident=ident)
        self.__lock = threading.Lock()  # protects virtual brightness
        self.__dimming = False

    def set_brightness(self, client: Optional[mqtt.Client], brightness: float):
        with self.__lock:
            ConcreteLight.set_brightness(self, client, brightness)

    def set_white_temp(self, client: Optional[mqtt.Client], temp: float):
        ConcreteLight.set_white_temp(self, client, temp)

    # pylint: disable=redefined-outer-name
    def set_color_temp(self, client: Optional[mqtt.Client], color: Color):
        ConcreteLight.set_color_temp(self, client, color)

    def is_dimmable(self) -> bool:
        return False

    def is_color(self) -> bool:
        return False

    def start_dim_down(self, client: mqtt.Client):
        self.__dimming = True
        threading.Thread(target=self.__pseudo_dim, args=(client, -1)).start()

    def start_dim_up(self, client: mqtt.Client):
        self.__dimming = True
        threading.Thread(target=self.__pseudo_dim, args=(client, +1)).start()

    def stop_dim(self, client: mqtt.Client):
        self.__dimming = False

    def update_state(self, client: mqtt.Client):
        if self.state.toggled_on and self.__over_threshold():
            client.publish(self.set_topic(), payload.state(True, self.kind))
        else:
            client.publish(self.set_topic(), payload.state(False, self.kind))

    def __over_threshold(self) -> bool:
        return self.state.brightness > self.BRIGHTNESS_THRESHOLD

    def __pseudo_dim(self, client: mqtt.Client, factor: int):
        speed = 0.2
        while self.__dimming:
            with self.__lock:
                new_brightness = self.state.brightness + factor*speed*self.DIMMING_SPEED
                super().set_brightness(client, new_brightness)
            time.sleep(speed)

class DimmableLight(Light):
    "A light of varying brightness."

    def __init__(self,
        name: str,
        room: str,
        vendor: Vendor,
        ident: str,
        kind: DeviceKind = DeviceKind.Light
    ):
        super().__init__(name=name, room=room, kind=kind, vendor=vendor, ident=ident)

    def is_dimmable(self) -> bool:
        return True

    def is_color(self) -> bool:
        return False

    def set_brightness(self, client: Optional[mqtt.Client], brightness: float):
        ConcreteLight.set_brightness(self, client, brightness)

    def set_white_temp(self, client: Optional[mqtt.Client], temp: float):
        ConcreteLight.set_white_temp(self, client, temp)

    # pylint: disable=redefined-outer-name
    def set_color_temp(self, client: Optional[mqtt.Client], color: Color):
        ConcreteLight.set_color_temp(self, client, color)

    def start_dim_down(self, client: mqtt.Client):
        client.publish(self.set_topic(), payload.start_dim(down=True))

    def start_dim_up(self, client: mqtt.Client):
        client.publish(self.set_topic(), payload.start_dim(down=False))

    def stop_dim(self, client: mqtt.Client):
        client.publish(self.set_topic(), payload.stop_dim())

    def update_state(self, client: mqtt.Client):
        if self.state.toggled_on:
            client.publish(self.set_topic(), payload.state(True, self.kind))
        else:
            client.publish(self.set_topic(), payload.state(False, self.kind))
        new_brightness = int(self.state.toggled_on) * self.state.brightness
        client.publish(self.set_topic(), payload.brightness(new_brightness))

class WhiteSpectrumLight(DimmableLight):
    "A light of varying brightness."

    def __init__(self,
        name: str,
        room: str,
        vendor: Vendor,
        ident: str,
        kind: DeviceKind = DeviceKind.Light
    ):
        super().__init__(name=name, room=room, kind=kind, vendor=vendor, ident=ident)

    def is_dimmable(self) -> bool:
        return True

    def is_color(self) -> bool:
        return False

    def update_state(self, client: mqtt.Client):
        super().update_state(client)
        load = payload.white_temp(self.state.white_temp, vendor=self.vendor)
        client.publish(self.set_topic(), load)

class ColorLight(DimmableLight):
    "A light of varying color"

    def __init__(self,
        name: str,
        room: str,
        vendor: Vendor,
        ident: str,
        kind: DeviceKind = DeviceKind.Light
    ):
        super().__init__(name=name, room=room, kind=kind, vendor=vendor, ident=ident)

    def is_color(self) -> bool:
        return True

    def update_state(self, client: mqtt.Client):
        super().update_state(client)
        load = payload.color(self.state.color, self.vendor)
        client.publish(self.set_topic(), load)

#######################################
##### LIGHT CREATION
#######################################

def simple(name: str, room: str, vendor: Vendor, kind: DeviceKind, ident: str) -> SimpleLight:
    "Creates a simple on-off light"
    return SimpleLight(name=name, room=room, vendor=vendor, kind=kind, ident=ident)

def dimmable(name: str, room: str, vendor: Vendor, ident: str) -> DimmableLight:
    "Creates a dimmable light"
    return DimmableLight(name=name, room=room, vendor=vendor, ident=ident)

def white(name: str, room: str, vendor: Vendor, ident: str) -> DimmableLight:
    "Creates a white spectrum light"
    return WhiteSpectrumLight(name=name, room=room, vendor=vendor, ident=ident)

def color(name: str, room: str, vendor: Vendor, ident: str) -> ColorLight:
    "Creates a color light"
    return ColorLight(name=name, room=room, vendor=vendor, ident=ident)
