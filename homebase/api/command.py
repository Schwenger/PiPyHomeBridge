"""
The logic for executing API commands
"""

import logging
from typing import Dict, Optional

import lighting
import lighting.config
from colour import Color
from comm import Payload, Topic
from enums import ApiCommand, TopicCategory
from home.home import Home
from homebaseerror import HomeBaseError
from paho.mqtt import client as mqtt
from sensor import Sensor


class Exec:
    "Executes API command."

    def __init__(self, home: Home, client: mqtt.Client):
        self.__home = home
        self.__client = client

    def exec(self, topic: Topic, cmd: ApiCommand, payload: Dict[str, str]):
        "Executes an API command."
        logging.info("Executing %s for %s", cmd, topic)
        {
            ApiCommand.Toggle:          lambda: self.__toggle(topic),
            ApiCommand.TurnOn:          lambda: self.__turn_on(topic),
            ApiCommand.TurnOff:         lambda: self.__turn_off(topic),
            ApiCommand.DimUp:           lambda: self.__dim_up(topic),
            ApiCommand.DimDown:         lambda: self.__dim_down(topic),
            ApiCommand.StartDimUp:      lambda: self.__start_dim_up(topic),
            ApiCommand.StartDimDown:    lambda: self.__start_dim_down(topic),
            ApiCommand.StopDimming:     lambda: self.__stop_dimming(topic),
            ApiCommand.EnableDynamic:   lambda: self.__set_dynamic(topic, True),
            ApiCommand.DisableDynamic:  lambda: self.__set_dynamic(topic, False),
            ApiCommand.EnableColorful:  lambda: self.__set_colorful(topic, True),
            ApiCommand.DisableColorful: lambda: self.__set_colorful(topic, False),
            ApiCommand.SetBrightness:   lambda: self.__set_brightness(topic, payload),
            ApiCommand.SetWhiteTemp:    lambda: self.__set_white_temp(topic, payload),
            ApiCommand.SetColor:        lambda: self.__set_color(topic, payload),
            ApiCommand.Rename:          lambda: self.__rename_device(topic, payload),
            ApiCommand.Refresh:         lambda: self.__refresh(topic),
            ApiCommand.QueryState:      lambda: self.__query_state(topic),
            ApiCommand.UpdateState:     lambda: self.__update_state(topic, payload),
        }[cmd]()

    def __get_abstract(self, topic: Topic) -> Optional[lighting.Abstract]:
        conc = self.__home.find_light(topic)
        if conc is not None:
            return conc
        for room in self.__home.rooms:
            if topic in [room.group.topic, room.topic]:
                return room.group
        return None

    def __get_abstract_force(self, topic: Topic) -> lighting.Abstract:
        res = self.__get_abstract(topic)
        if res is None:
            logging.error("Cannot find device for %s", topic.string)
            raise HomeBaseError.DeviceNotFound
        return res

    def __get_sensor(self, topic: Topic) -> Optional[Sensor]:
        return self.__home.find_sensor(topic)

    def __toggle(self, topic: Topic):
        light = self.__get_abstract_force(topic)
        light.toggle(self.__client)
        if light.state.toggled_on:
            self.__refresh_single(light)

    def __turn_on(self, topic: Topic):
        light = self.__get_abstract_force(topic)
        light.turn_on(self.__client)
        self.__refresh_single(light)

    def __turn_off(self, topic: Topic):
        light = self.__get_abstract_force(topic)
        light.turn_off(self.__client)

    def __dim_up(self, topic: Topic):
        light = self.__get_abstract_force(topic)
        light.dim_up()
        self.__refresh(topic)

    def __dim_down(self, topic: Topic):
        light = self.__get_abstract_force(topic)
        light.dim_down()
        self.__refresh(topic)

    def __start_dim_up(self, topic: Topic):
        light = self.__get_abstract_force(topic)
        light.start_dim_up(self.__client)

    def __start_dim_down(self, topic: Topic):
        light = self.__get_abstract_force(topic)
        light.start_dim_down(self.__client)

    def __stop_dimming(self, topic: Topic):
        light = self.__get_abstract_force(topic)
        light.stop_dim(self.__client)
        self.__query_state(topic)

    def __set_dynamic(self, topic: Topic, val: bool):
        abstract = self.__get_abstract_force(topic)
        abstract.override_dynamic(val)
        self.__refresh(topic)

    def __set_colorful(self, topic: Topic, val: bool):
        abstract = self.__get_abstract_force(topic)
        abstract.override_colorful(val)
        self.__refresh(topic)

    def __set_brightness(self, topic: Topic, payload: Dict[str, str]):
        light = self.__get_abstract_force(topic)
        brightness = float(payload["brightness"])
        light.set_brightness(brightness)
        self.__refresh(topic)

    def __set_white_temp(self, topic: Topic, payload: Dict[str, str]):
        light = self.__get_abstract_force(topic)
        white_temp = float(payload["white"])
        light.set_white_temp(self.__client, white_temp)

    def __set_color(self, topic: Topic, payload: Dict[str, str]):
        light = self.__get_abstract_force(topic)
        color = Color(payload["color"])
        light.set_color_temp(color)
        self.__refresh(topic)

    def __rename_device(self, topic: Topic, payload: Dict[str, str]):
        # ToDo
        raise NotImplementedError
        # pay = Payload.rename(topic.without_base, payload["new_name"])
        # target = Topic.for_bridge(["request", "device"], "rename")
        # self.__client.publish(target.string, payload=pay)

    def __refresh(self, topic: Topic):
        logging.debug("Refreshing Topic.")
        if topic.category == TopicCategory.Home:
            return self.__refresh_home()
        target = self.__get_abstract_force(topic)
        logging.debug("Refreshing abstract.")
        for light in target.flatten_lights():
            self.__refresh_single(light)

    def __refresh_home(self):
        logging.debug("Refreshing home.")
        for room in self.__home.rooms:
            self.__refresh(room.group.topic)

    def __refresh_single(self, light: lighting.Abstract):
        logging.debug("Refreshing Single")
        dynamic = lighting.dynamic.recommended()
        logging.debug(dynamic)
        config = self.__home.compile_config(light.topic)
        logging.debug(config)
        assert config is not None
        target = lighting.config.resolve(config, dynamic)
        logging.debug(target)
        if light.state.toggled_on and target.toggled_on:
            light.realize_state(self.__client, target)

    def __query_state(self, topic: Topic):
        payload = Payload().state(None).finalize()
        self.__client.publish(topic.as_get(), payload=payload)

    def __update_state(self, topic: Topic, payload: Dict[str, str]):
        light = self.__get_abstract(topic)
        if light is not None:
            return self.__update_light_state(light, payload)
        sensor = self.__get_sensor(topic)
        if sensor is not None:
            return self.__update_sensor_state(sensor, payload)
        raise HomeBaseError.DeviceNotFound

    def __update_light_state(self, target: lighting.Collection, payload: Dict[str, str]):
        if not isinstance(target, lighting.Concrete):
            raise HomeBaseError.InvalidPhysicalQuery
        state = lighting.State.read_light_state(payload)
        target.update_virtual_state(state)

    def __update_sensor_state(self, target: Sensor, payload: Dict[str, str]):
        for key in payload:
            quant = Payload.sensor_quant_mapping().get(key)
            if quant is None:
                continue
            try:
                val = float(payload[key])
                target.update_state(quant, val)
            except ValueError as exc:
                logging.warning("Invalid quantity for sensor update: Not a float. %s", payload[key])
                raise HomeBaseError.InvalidPhysicalQuantity from exc
