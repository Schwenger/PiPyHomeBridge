"""
The logic for executing API commands
"""

from typing import Dict
import logging

import lighting
import lighting.config
from colour import Color
from comm import Payload, Topic
from enums import ApiCommand, TopicCategory
from home.home import Home
from homebaseerror import HomeBaseError
from paho.mqtt import client as mqtt


class Exec:
    "Executes API command."

    def __init__(self, home: Home, client: mqtt.Client):
        self.__home = home
        self.__client = client

    def exec(self, topic: Topic, cmd: ApiCommand, payload: Dict[str, str]):
        "Executes an API command."
        {
            ApiCommand.Toggle:                lambda: self.__toggle(topic),
            ApiCommand.TurnOn:                lambda: self.__turn_on(topic),
            ApiCommand.TurnOff:               lambda: self.__turn_off(topic),
            ApiCommand.DimUp:                 lambda: self.__dim_up(topic),
            ApiCommand.DimDown:               lambda: self.__dim_down(topic),
            ApiCommand.StartDimUp:            lambda: self.__start_dim_up(topic),
            ApiCommand.StartDimDown:          lambda: self.__start_dim_down(topic),
            ApiCommand.StopDimming:           lambda: self.__stop_dimming(topic),
            ApiCommand.EnableDynamicDimming:  None,
            ApiCommand.DisableDynamicDimming: None,
            ApiCommand.EnableDynamicColor:    None,
            ApiCommand.DisableDynamicColor:   None,
            ApiCommand.SetBrightness:         lambda: self.__set_brightness(topic, payload),
            ApiCommand.SetWhiteTemp:          lambda: self.__set_white_temp(topic, payload),
            ApiCommand.SetColor:              lambda: self.__set_color(topic, payload),
            ApiCommand.Rename:                lambda: self.__rename_device(topic, payload),
            ApiCommand.Refresh:               self.__refresh,
            ApiCommand.QueryPhysicalState:    lambda: self.__query_physical_state(topic),
            ApiCommand.UpdateVirtualState:    lambda: self.__update_virtual_state(topic, payload),
            ApiCommand.UpdateSensorState:     lambda: self.__update_sensor_state(topic, payload),
        }[cmd]()

    def __get_target(self, topic: Topic) -> lighting.Collection:
        logging.debug(topic)
        light = self.__home.find_light(topic)
        if light is not None:
            return light
        room = self.__home.room_by_name(topic.name)
        if room is None:
            raise HomeBaseError.RoomNotFound
        return room.group

    def __toggle(self, topic: Topic):
        coll = self.__get_target(topic)
        for light in coll.flatten_lights():
            light.toggle(self.__client)
            if light.state.toggled_on:
                self.__refresh_single(light)

    def __turn_on(self, topic: Topic):
        coll = self.__get_target(topic)
        for light in coll.flatten_lights():
            light.turn_on(self.__client)
            self.__refresh_single(light)

    def __turn_off(self, topic: Topic):
        coll = self.__get_target(topic)
        for light in coll.flatten_lights():
            light.turn_off(self.__client)

    def __dim_up(self, topic: Topic):
        coll = self.__get_target(topic)
        for light in coll.flatten_lights():
            light.dim_up(self.__client)

    def __dim_down(self, topic: Topic):
        coll = self.__get_target(topic)
        for light in coll.flatten_lights():
            light.dim_down(self.__client)

    def __start_dim_up(self, topic: Topic):
        coll = self.__get_target(topic)
        for light in coll.flatten_lights():
            light.start_dim_up(self.__client)

    def __start_dim_down(self, topic: Topic):
        coll = self.__get_target(topic)
        for light in coll.flatten_lights():
            light.start_dim_down(self.__client)

    def __stop_dimming(self, topic: Topic):
        coll = self.__get_target(topic)
        for light in coll.flatten_lights():
            light.stop_dim(self.__client)

    def __set_brightness(self, topic: Topic, payload: Dict[str, str]):
        coll = self.__get_target(topic)
        for light in coll.flatten_lights():
            brightness = float(payload["brightness"])
            light.set_brightness(self.__client, brightness)

    def __set_white_temp(self, topic: Topic, payload: Dict[str, str]):
        coll = self.__get_target(topic)
        for light in coll.flatten_lights():
            white_temp = float(payload["white"])
            light.set_white_temp(self.__client, white_temp)

    def __set_color(self, topic: Topic, payload: Dict[str, str]):
        coll = self.__get_target(topic)
        for light in coll.flatten_lights():
            color = Color(payload["color"])
            light.set_color_temp(self.__client, color)

    def __rename_device(self, topic: Topic, payload: Dict[str, str]):
        pay = Payload.rename(topic.without_base, payload["new_name"])
        target = Topic.for_bridge(["request", "device"], "rename")
        self.__client.publish(target.string, payload=pay)

    def __refresh(self):
        for light in self.__home.flatten_lights():
            self.__refresh_single(light)

    def __refresh_single(self, light: lighting.Concrete):
        dynamic = lighting.dynamic.recommended()
        config = self.__home.compile_config(light.topic)
        assert config is not None
        target = lighting.config.resolve(config, dynamic)
        if light.state.toggled_on and target.toggled_on:
            light.realize_state(self.__client, target)

    def __query_physical_state(self, topic: Topic):
        target = self.__get_target(topic)
        if not isinstance(target, lighting.Concrete):
            raise HomeBaseError.InvalidPhysicalQuery
        payload = Payload()
        payload.state(None)
        self.__client.publish(topic.as_get(), payload=payload.finalize())

    def __update_virtual_state(self, topic: Topic, payload: Dict[str, str]):
        target = self.__get_target(topic)
        if not isinstance(target, lighting.Concrete):
            raise HomeBaseError.InvalidPhysicalQuery
        state = lighting.State.read_light_state(payload)
        target.update_virtual_state(state)

    def __update_sensor_state(self, topic: Topic, payload: Dict[str, str]):
        target = self.__home.find_sensor(topic)
        logging.debug("Updating sensor with payload %s.", payload)
        if target is None:
            logging.warning("Failed to find sensor.")
            raise HomeBaseError.SensorNotFound
        for key in payload:
            logging.debug("Found key: %s", key)
            quant = Payload.sensor_quant_mapping().get(key)
            logging.debug("Results in quantity %s", quant)
            if quant is None:
                continue
            try:
                val = float(payload[key])
                target.update_state(quant, val)
            except ValueError as exc:
                logging.warning("Invalid quantity for sensor update: Not a float. %s", payload[key])
                raise HomeBaseError.InvalidPhysicalQuantity from exc
