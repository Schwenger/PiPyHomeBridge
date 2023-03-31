"Different types of light sources."

import threading
import time
from typing import Optional

from comm import Payload
from lighting.source import Abstract, Concrete
from paho.mqtt import client as mqtt
from enums import DeviceModel


class SimpleLight(Concrete, Abstract):
    "A simple on-off light"

    BRIGHTNESS_THRESHOLD = 0.33
    DIMMING_SPEED = 0.2

    def __init__(
        self,
        name: str,
        room: str,
        icon: str,
        model: DeviceModel,
        ident: str,
    ):
        super().__init__(
            name=name,
            room=room,
            icon=icon,
            model=model,
            ident=ident
        )
        self.__lock = threading.Lock()  # protects virtual brightness
        self.__dimming = False

    ################################################
    # Overriding Functions
    ################################################
    def start_dim_down(self, client: mqtt.Client):
        self.__dimming = True
        threading.Thread(target=self.__pseudo_dim, args=(client, -1)).start()

    def start_dim_up(self, client: mqtt.Client):
        self.__dimming = True
        threading.Thread(target=self.__pseudo_dim, args=(client, +1)).start()

    def stop_dim(self, client: mqtt.Client):
        self.__dimming = False

    def state_change_payload(self) -> Optional[Payload]:
        physically_on = self.state.toggled_on and self.__over_threshold()
        return Payload().state(toggled_on=physically_on)

    ################################################
    # Private Functions
    ################################################

    def __over_threshold(self) -> bool:
        return self.state.brightness > self.BRIGHTNESS_THRESHOLD

    def __pseudo_dim(self, client: mqtt.Client, factor: int):
        speed = 0.2
        while self.__dimming:
            with self.__lock:
                new_brightness = self.state.brightness + factor * speed * self.DIMMING_SPEED
                super().set_brightness(client, new_brightness)
            time.sleep(speed)


class RegularLight(Concrete):
    "A light of varying brightness."

    def __init__(
        self,
        name: str,
        room: str,
        icon: str,
        ident: str,
        model: DeviceModel
    ):
        super().__init__(
            name=name,
            room=room,
            icon=icon,
            model=model,
            ident=ident
        )

#######################################
# LIGHT CREATION
#######################################


def simple(name: str, room: str, icon: str, ident: str, model: DeviceModel) -> SimpleLight:
    "Creates a simple on-off light"
    return SimpleLight(
        name=name,
        room=room,
        icon=icon,
        model=model,
        ident=ident
    )


def regular(name: str, room: str, icon: str, ident: str, model: DeviceModel) -> RegularLight:
    "Creates a dimmable light"
    return RegularLight(name=name, room=room, icon=icon, ident=ident, model=model)
