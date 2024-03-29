"Represents a collection of light sources."

from typing import List, Optional

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
        room:          str,
        groups:        List['Group'],
        hierarchie:    List[str],
        config:        Config,
    ):
        super().__init__(config=config)
        self.name:          str               = name
        self.room:          str               = room
        self.groups:        List[Group]       = groups
        self.hierarchie:    List[str]         = hierarchie
        self.single_lights: List[Concrete]    = single_lights

    @property
    def topic(self) -> Topic:
        return Topic.for_group(
            room = self.room,
            hierarchie = self.hierarchie,
            name = self.name,
        )

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
    def is_white_spec(self) -> bool:
        return any(map(lambda l: l.is_white_spec, self.all_lights))

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
