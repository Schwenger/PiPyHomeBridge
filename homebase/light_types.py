"Different types of light sources."

import time
from typing import Optional
import threading
from colour import Color
from paho.mqtt import client as mqtt
from light import Light, ConcreteLight
from payload import Payload
from enums import DeviceModel


class SimpleLight(Light):
    "A simple on-off light"

    BRIGHTNESS_THRESHOLD = 0.33
    DIMMING_SPEED = 0.2

    def __init__(
        self,
        name: str,
        room: str,
        model: DeviceModel,
        ident: str,
    ):
        super().__init__(
            name=name,
            room=room,
            model=model,
            ident=ident
        )
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

    def state_change_payload(self) -> Optional[Payload]:
        physically_on = self.state.toggled_on and self.__over_threshold()
        return Payload().state(toggled_on=physically_on)

    def __over_threshold(self) -> bool:
        return self.state.brightness > self.BRIGHTNESS_THRESHOLD

    def __pseudo_dim(self, client: mqtt.Client, factor: int):
        speed = 0.2
        while self.__dimming:
            with self.__lock:
                new_brightness = self.state.brightness + factor * speed * self.DIMMING_SPEED
                super().set_brightness(client, new_brightness)
            time.sleep(speed)


class DimmableLight(Light):
    "A light of varying brightness."

    def __init__(
        self,
        name: str,
        room: str,
        ident: str,
        model: DeviceModel
    ):
        super().__init__(
            name=name,
            room=room,
            model=model,
            ident=ident
        )

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
        client.publish(self.set_topic(), Payload.start_dim(down=True))

    def start_dim_up(self, client: mqtt.Client):
        client.publish(self.set_topic(), Payload.start_dim(down=False))

    def stop_dim(self, client: mqtt.Client):
        client.publish(self.set_topic(), Payload.stop_dim())

    def state_change_payload(self) -> Optional[Payload]:
        "Creates a payload to realize the current virtual state."
        payload = Payload().state(self.state.toggled_on)
        new_brightness = int(self.state.toggled_on) * self.state.brightness
        return payload.brightness(new_brightness)


class WhiteSpectrumLight(DimmableLight):
    "A light of varying brightness."

    def __init__(
        self,
        name: str,
        room: str,
        model: DeviceModel,
        ident: str,
    ):
        super().__init__(
            name=name,
            room=room,
            model=model,
            ident=ident
        )

    def is_dimmable(self) -> bool:
        return True

    def is_color(self) -> bool:
        return False

    def state_change_payload(self) -> Optional[Payload]:
        payload = super().state_change_payload()
        if payload is None:
            return None
        new_white = int(self.state.toggled_on) * self.state.white_temp
        return payload.white_temp(new_white, vendor=self.vendor)


class ColorLight(DimmableLight):
    "A light of varying color"

    def __init__(
        self,
        name: str,
        room: str,
        ident: str,
        model: DeviceModel,
    ):
        super().__init__(
            name=name,
            room=room,
            model=model,
            ident=ident,
        )

    def is_color(self) -> bool:
        return True

    def state_change_payload(self) -> Optional[Payload]:
        payload = super().state_change_payload()
        if payload is None:
            return None
        return payload.color(self.state.color, self.vendor)

#######################################
# LIGHT CREATION
#######################################


def simple(name: str, room: str, ident: str, model: DeviceModel) -> SimpleLight:
    "Creates a simple on-off light"
    return SimpleLight(
        name=name,
        room=room,
        model=model,
        ident=ident
    )


def dimmable(name: str, room: str, ident: str, model: DeviceModel) -> DimmableLight:
    "Creates a dimmable light"
    return DimmableLight(name=name, room=room, ident=ident, model=model)


def white(name: str, room: str, ident: str, model: DeviceModel) -> DimmableLight:
    "Creates a white spectrum light"
    return WhiteSpectrumLight(name=name, room=room, ident=ident, model=model)


def color(name: str, room: str, ident: str, model: DeviceModel) -> ColorLight:
    "Creates a color light"
    return ColorLight(name=name, room=room, ident=ident, model=model)
