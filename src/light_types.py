"Different types of light sources."

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
            print("DimmableLight: Turn on")
            client.publish(self.set_topic(), payload.on)
        else:
            print("DimmableLight: Turn off")
            client.publish(self.set_topic(), payload.off)
        new_brightness = int(self.state.toggled_on) * self.state.brightness
        print("DimmableLight: Setting brightness to " + str(new_brightness))
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
        print("WhiteLight: Update State")
        super().update_state(client)
        print("WhiteLight: Setting white to " + str(self.state.white_temp))
        client.publish(self.set_topic(), payload.hue_color_temp(self.state.white_temp))

class ColorLight(DimmableLight):
    "A light of varying color"

    def __init__(self, name: str, room: str, kind: str = "Light"):
        super().__init__(name=name, room=room, kind=kind)

    def is_color(self) -> bool:
        "Determines if the light can display different colors"
        return True

    def update_state(self, client: mqtt.Client):
        print("ColorLight: Update State")
        super().update_state(client)
        print("ColorLight: Setting white to " + str(self.state.color))
        client.publish(self.set_topic(), payload.color(self.state.color))

class SimpleLight(Light):
    "A simple on-off light"

    BRIGHTNESS_THRESHOLD = 0.33

    def __init__(self, name: str, room: str, kind="Light"):
        super().__init__(name=name, room=room, kind=kind)
        self.__lock = threading.Lock()
        # pylint: disable=unused-private-member
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

    def pseudo_dim(self, _client: mqtt.Client, _factor: int):
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
        # pylint: disable=unused-private-member
        self.__dimming = True

    def start_dim_up(self, client: mqtt.Client):
        "Starts gradually reducing the brightness."
        threading.Thread(target=self.pseudo_dim, args=(client, +1)).start()
        # pylint: disable=unused-private-member
        self.__dimming = True

    def stop_dim(self, client: mqtt.Client):
        "Starts gradually reducing the brightness."
        # pylint: disable=unused-private-member
        self.__dimming = False

    def over_threshold(self) -> bool:
        "Returns true if the virtual brightness suggests this light should be on."
        return self.state.brightness > self.BRIGHTNESS_THRESHOLD

    def update_state(self, client: mqtt.Client):
        print("SimpleLight: Update State")
        if self.state.toggled_on and self.over_threshold():
            print("SimpleLight: turn on")
            client.publish(self.set_topic(), payload.on)
        else:
            print("SimpleLight: turn off")
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
