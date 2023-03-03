"Represents a collection of light sources."

from typing import List
from paho.mqtt import client as mqtt
from light import LightState, AbstractLight
import dynamic_light

class LightGroup(AbstractLight):
    """
        A collection of abstract lights.
        Has additional configurative options like colorful mode or adaptive dimming.
    """

    def __init__(self, lights: List[AbstractLight], adaptive: bool, colorful: bool):
        self.adaptive: bool = adaptive
        self.colorful: bool = colorful
        self.lights: List[AbstractLight] = lights

    @property
    def state(self) -> LightState:
        return LightState.average(list(map(lambda l: l.state, self.lights)))

    ################################################
    ##### CONFIGURATIVE API
    ################################################
    def enable_adaptive_dimming(self):
        "Enables AdaptiveDimming"
        self.adaptive = True

    def disable_adaptive_dimming(self):
        "Disables AdaptiveDimming"
        self.adaptive = False

    def enable_colorful(self):
        "Enables Colorful"
        self.colorful = True

    def disable_colorful(self):
        "Disables Colorful"
        self.colorful = False

    ################################################
    ##### INFORMATIONAL API
    ################################################
    def is_dimmable(self) -> bool:
        return any(map(AbstractLight.is_dimmable, self.lights))

    def is_color(self) -> bool:
        return any(map(AbstractLight.is_color, self.lights))

    ################################################
    ##### COLLECTION API
    ################################################

    def refresh(self, client):
        "Refreshes the light state of all lights according to config."
        for light in self.lights:
            self._refresh(client, light)

    ################################################
    ##### FUNCTIONAL API
    ################################################

    def realize_state(self, client: mqtt.Client, state: LightState):
        for light in self.lights:
            light.realize_state(client, state)

    def start_dim_down(self, client: mqtt.Client):
        for light in self.lights:
            light.start_dim_down(client)

    def start_dim_up(self, client: mqtt.Client):
        for light in self.lights:
            light.start_dim_up(client)

    def stop_dim(self, client: mqtt.Client):
        for light in self.lights:
            light.stop_dim(client)

    def turn_on(self, client: mqtt.Client):
        for light in self.lights:
            light.turn_on(client)
            self._refresh(client, light)

    def turn_off(self, client: mqtt.Client):
        for light in self.lights:
            light.turn_off(client)

    def toggle(self, client: mqtt.Client):
        for light in self.lights:
            light.toggle(client)
            if light.state.toggled_on:
                self._refresh(client, light)

    def shift_color_clockwise(self, client: mqtt.Client):
        for light in self.lights:
            light.shift_color_clockwise(client)

    def shift_color_counter_clockwise(self, client: mqtt.Client):
        for light in self.lights:
            light.shift_color_counter_clockwise(client)

    def dim_up(self, client: mqtt.Client):
        for light in self.lights:
            light.dim_up(client)

    def dim_down(self, client: mqtt.Client):
        for light in self.lights:
            light.dim_down(client)

    ################################################
    ##### PROTECTED
    ################################################

    def _any_on(self) -> bool:
        return any(map(lambda l: l.state.toggled_on, self.lights))

    def _refresh(self, client, light: AbstractLight):
        target_state = dynamic_light.recommended()
        light.realize_state(client, target_state)
