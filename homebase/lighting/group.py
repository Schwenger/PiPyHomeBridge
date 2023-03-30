"Represents a collection of light sources."

from typing import List, Optional

from colour import Color
from comm import Topic
from lighting.config import Config
from lighting.source import Abstract, Collection, Concrete
from lighting.state import State
from paho.mqtt import client as mqtt


class Group(Abstract, Collection):
    """
        A collection of abstract lights.
        Has additional configurative options like colorful mode or adaptive dimming.
    """

    def __init__(
        self,
        single_lights: List[Concrete],
        name:          str,
        groups:        List['Group'],
        hierarchie:    List[str]
    ):
        super().__init__(config=Config())
        self.name:          str               = name
        self.groups:        List[Group]       = groups
        self.hierarchie:    List[str]         = hierarchie
        self.single_lights: List[Concrete]    = single_lights

    @property
    def state(self) -> State:
        return State.average(list(map(lambda lig: lig.state, self.all_lights)))

    @property
    def topic(self) -> Topic:
        return Topic.for_group(self.hierarchie)

    @property
    def all_lights(self) -> List[Abstract]:
        "Returns a list of all abstract lights"
        return self.single_lights + self.groups  # type: ignore

    def compile_config(self, topic: Topic) -> Optional[Config]:
        """
            Compiles the light configuration for a light with the given topic.
            Returns None if the light is not a member of this group.
        """
        cfg = self.config
        if topic == self.topic:
            return cfg
        for light in self.all_lights:
            if light.topic == topic:
                return light.config.with_parent(cfg)
        for group in self.groups:
            res = group.compile_config(topic)
            if res is not None:
                return res.with_parent(cfg)
        return None

    ################################################
    # INFORMATIONAL API
    ################################################
    @property
    def is_dimmable(self) -> bool:
        return any(map(lambda l: l.is_dimmable, self.all_lights))

    @property
    def is_color(self) -> bool:
        return any(map(lambda l: l.is_color, self.all_lights))

    ################################################
    # COLLECTION API
    ################################################

    def flatten_lights(self) -> List[Concrete]:
        return self.single_lights + sum(map(lambda grp: grp.flatten_lights(), self.groups), [])

    ################################################
    # FUNCTIONAL API
    ################################################

    def realize_state(self, client: mqtt.Client, state: State):
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
            light.turn_on(client)

    def turn_off(self, client: mqtt.Client):
        for light in self.all_lights:
            light.turn_off(client)

    def toggle(self, client: mqtt.Client):
        for light in self.all_lights:
            light.toggle(client)

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
        return any(map(lambda light: light.state.toggled_on, self.all_lights))
