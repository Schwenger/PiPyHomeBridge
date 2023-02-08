"Represents a collection of light sources."

from abc import abstractmethod
from typing import Optional, List
from paho.mqtt import client as mqtt
from lights import Light
from light_config import LightConfig
from room_config import RoomConfig
from payload import RoutingResult, Topic

class LightCollection:
    "Represents a collection of light sources."

    def __init__(self, lights: List[Light], adaptive: bool, colorful: bool):
        self.lights: List[Light] = lights
        self.room_config: RoomConfig = RoomConfig(
            self.lights,
            self._bias_for,
            adaptive=adaptive,
            colorful=colorful
        )

    @abstractmethod
    def _bias_for(self, light: Light) -> int:
        "Defines the bias for a given light."

    def find_light(self, topic: Topic) -> Optional[Light]:
        "Find the device with the given topic."
        return next((item for item in self.lights if item.name == topic.name), None)

    def route_message(self, client: mqtt.Client, topic: Topic, payload) -> RoutingResult:
        "Routes the message to the device based on the topic."
        light = self._light_by_name(topic.name)
        if light is not None:
            light.consume_message(client, payload)
            return RoutingResult.ACCEPT
        return RoutingResult.NOT_FOUND

    def refresh_lights(self, client, override_on_off: bool = False):
        "Adapts the lights to the current time of day.  Should be called periodically."
        self._apply_config(client, override_on_off)

    def toggle_lights(self, client: mqtt.Client):
        "toggles all lights"
        if self._any_on():
            self._apply_config(client, override_on_off=True, cfg=LightConfig.off())
        else:
            self.refresh_lights(client, override_on_off=True)

    def lights_on(self, client: mqtt.Client):
        "turn all lights on"
        if not self._any_on():
            self.refresh_lights(client, override_on_off=True)

    def lights_off(self, client: mqtt.Client):
        "turn all lights off"
        self._apply_config(client, override_on_off=True, cfg=LightConfig.off())

    def shift_color_clockwise(self, client: mqtt.Client):
        "Shift color clockwise"
        self.room_config.shift_color_clockwise()
        self.refresh_lights(client)

    def shift_color_counter_clockwise(self, client: mqtt.Client):
        "Shift color counter clockwise"
        self.room_config.shift_color_counter_clockwise()
        self.refresh_lights(client)

    def dim(self, client: mqtt.Client):
        "Dim the lights in the room"
        self.room_config.dim()
        self.refresh_lights(client)

    def brighten(self, client: mqtt.Client):
        "Brighten the lights in the room"
        self.room_config.brighten()
        self.refresh_lights(client)

    def start_dim_down(self, client: mqtt.Client):
        "Starts dimming the lights"
        for light in self.lights:
            light.start_dim_down(client)

    def start_dim_up(self, client: mqtt.Client):
        "Starts dimming the lights"
        for light in self.lights:
            light.start_dim_up(client)

    def stop_dim(self, client: mqtt.Client):
        "Stops dimming the lights"
        for light in self.lights:
            light.stop_dim(client)

    def enable_adaptive_dimming(self, client: mqtt.Client):
        "Enables AdaptiveDimming"
        self.room_config.adaptive = True
        self.refresh_lights(client)

    def disable_adaptive_dimming(self, client: mqtt.Client):
        "Disables AdaptiveDimming"
        self.room_config.adaptive = False
        self.refresh_lights(client)

    def enable_colorful(self, client: mqtt.Client):
        "Enables Colorful"
        self.room_config.colorful = True
        self.refresh_lights(client)

    def disable_colorful(self, client: mqtt.Client):
        "Disables Colorful"
        self.room_config.colorful = False
        self.refresh_lights(client)

    def _apply_config(
            self,
            client: mqtt.Client,
            override_on_off: bool,
            cfg: Optional[LightConfig] = None
        ):
        for light in self.lights:
            target_cfg = cfg or self._get_current_config(light)
            changes_on_off_status = light.is_on() != target_cfg.is_on
            if changes_on_off_status and not override_on_off:
                continue
            light.apply_config(client, target_cfg)

    def _get_current_config(self, light: Light) -> LightConfig:
        "Returns the appropriate LightConfig for the given light, time of day, and LightFlow state."
        cfg  = LightConfig.recommended()
        cfg = self.room_config.adapt_config(light, cfg)
        return cfg

    def _light_by_name(self, name: str) -> Optional[Light]:
        "Finds the light with the given name in the room."
        return next((light for light in self.lights if light.name == name), None)

    def _any_on(self):
        "Returns whether at least on light is on."
        return any(map(Light.is_on, self.lights))
