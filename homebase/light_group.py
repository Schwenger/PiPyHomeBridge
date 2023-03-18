"Represents a collection of light sources."

from typing import List, Optional
from colour import Color
from paho.mqtt import client as mqtt
from light import Light, LightState, AbstractLight
from topic import Topic
import dynamic_light


class LightGroup(AbstractLight):
    """
        A collection of abstract lights.
        Has additional configurative options like colorful mode or adaptive dimming.
    """

    def __init__(
        self,
        single_lights:     List[Light],
        name: str,
        groups:     List['LightGroup'],
        adaptive:   bool,
        colorful:   bool,
        hierarchie: List[str]
    ):
        self.name: str = name
        self.adaptive:      bool                = adaptive
        self.colorful:      bool                = colorful
        self.groups:        List[LightGroup]    = groups
        self.hierarchie:    List[str]           = hierarchie
        self.single_lights: List[Light]         = single_lights

    @property
    def state(self) -> LightState:
        return LightState.average(list(map(lambda l: l.state, self.all_lights)))

    @property
    def topic(self) -> Topic:
        return Topic.for_group(self.hierarchie)

    @property
    def all_lights(self) -> List[AbstractLight]:
        "Returns a list of all abstract lights"
        return self.single_lights + self.groups  # type: ignore

    ################################################
    # CONFIGURATIVE API
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
    # INFORMATIONAL API
    ################################################
    def is_dimmable(self) -> bool:
        return any(map(AbstractLight.is_dimmable, self.all_lights))

    def is_color(self) -> bool:
        return any(map(AbstractLight.is_color, self.all_lights))

    ################################################
    # COLLECTION API
    ################################################

    def refresh(self, client):
        "Refreshes the light state of all lights according to config."
        for light in self.all_lights:
            self._refresh(client, light)

    def flatten_lights(self) -> List[Light]:
        "Returns a flat list of lights appearing in this group."
        res = self.single_lights
        for group in self.groups:
            res += group.flatten_lights()
        return res

    ################################################
    # FUNCTIONAL API
    ################################################

    def realize_state(self, client: mqtt.Client, state: LightState):
        for light in self.all_lights:
            light.realize_state(client, state)

    def start_dim_down(self, client: mqtt.Client):
        for light in self.all_lights:
            light.start_dim_down(client)

    def start_dim_up(self, client: mqtt.Client):
        for light in self.all_lights:
            light.start_dim_up(client)

    def stop_dim(self, client: mqtt.Client):
        for light in self.all_lights:
            light.stop_dim(client)

    def turn_on(self, client: mqtt.Client):
        for light in self.all_lights:
            self._refresh(client, light)
            light.turn_on(client)

    def turn_off(self, client: mqtt.Client):
        for light in self.all_lights:
            light.turn_off(client)

    def toggle(self, client: mqtt.Client):
        for light in self.all_lights:
            light.toggle(client)
            if light.state.toggled_on:
                self._refresh(client, light)

    def shift_color_clockwise(self, client: mqtt.Client):
        for light in self.all_lights:
            light.shift_color_clockwise(client)

    def shift_color_counter_clockwise(self, client: mqtt.Client):
        for light in self.all_lights:
            light.shift_color_counter_clockwise(client)

    def dim_up(self, client: mqtt.Client):
        for light in self.all_lights:
            light.dim_up(client)

    def dim_down(self, client: mqtt.Client):
        for light in self.all_lights:
            light.dim_down(client)

    def set_brightness(self, client: Optional[mqtt.Client], brightness: float):
        for light in self.all_lights:
            light.set_brightness(client, brightness)

    def set_white_temp(self, client: Optional[mqtt.Client], temp: float):
        for light in self.all_lights:
            light.set_white_temp(client, temp)

    def set_color_temp(self, client: Optional[mqtt.Client], color: Color):
        for light in self.all_lights:
            light.set_color_temp(client, color)

    ################################################
    # PROTECTED
    ################################################

    def _any_on(self) -> bool:
        return any(map(lambda l: l.state.toggled_on, self.all_lights))

    def _refresh(self, client, light: AbstractLight):
        target_state = dynamic_light.recommended()
        if light.state.toggled_on and target_state.toggled_on:
            light.realize_state(client, target_state)
