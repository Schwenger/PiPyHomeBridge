"""
The logic for executing API commands
"""

from typing import Callable, Dict

import lighting
import lighting.config
from api.api_common import (get_abstract, get_abstract_force,
                            get_configured_state, get_sensor)
from comm import Payload, Topic
from common import Log
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
        Log.api.info("Executing command %s for %s", cmd, topic)
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
            # ApiCommand.SetWhiteTemp:    lambda: self.__set_white_temp(topic, payload),
            # ApiCommand.SetColor:        lambda: self.__set_color(topic, payload),
            ApiCommand.Rename:          lambda: self.__rename_device(topic, payload),
            ApiCommand.Refresh:         lambda: self.__refresh(topic),
            ApiCommand.QueryState:      lambda: self.__query_state(topic),
            ApiCommand.UpdateState:     lambda: self.__update_state(topic, payload),
        }[cmd]()

    def __light_operation(self, topic: Topic, func: Callable[[lighting.Abstract], None]):
        light = get_abstract_force(topic, self.__home)
        func(light)
        self.__refresh_single(light)

    def __toggle(self, topic: Topic):
        self.__light_operation(topic, lighting.Abstract.toggle)

    def __turn_on(self, topic: Topic):
        self.__light_operation(topic, lighting.Abstract.turn_on)

    def __turn_off(self, topic: Topic):
        self.__light_operation(topic, lighting.Abstract.turn_off)

    def __dim_up(self, topic: Topic):
        self.__light_operation(topic, lighting.Abstract.dim_up)

    def __dim_down(self, topic: Topic):
        self.__light_operation(topic, lighting.Abstract.dim_down)

    def __start_dim_up(self, topic: Topic):
        light = get_abstract_force(topic, home=self.__home)
        light.start_dim_up(self.__client)

    def __start_dim_down(self, topic: Topic):
        light = get_abstract_force(topic, home=self.__home)
        light.start_dim_down(self.__client)

    def __stop_dimming(self, topic: Topic):
        light = get_abstract_force(topic, home=self.__home)
        light.stop_dim(self.__client)
        self.__query_state(topic)

    def __set_dynamic(self, topic: Topic, val: bool):
        self.__light_operation(topic, lambda light: light.set_dynamic(val))

    def __set_colorful(self, topic: Topic, val: bool):
        self.__light_operation(topic, lambda light: light.set_colorful(val))

    def __set_brightness(self, topic: Topic, payload: Dict[str, str]):
        brightness = float(payload["brightness"])
        def func(light: lighting.Abstract):
            current = get_configured_state(self.__home, light)
            light.accommodate_brightness(desired=brightness, actual=current.brightness)
        self.__light_operation(topic=topic, func=func)

    # def __set_white_temp(self, topic: Topic, payload: Dict[str, str]):
    #     light = self.__get_abstract_force(topic)
    #     white_temp = float(payload["white"])
    #     light.set_white_temp(self.__client, white_temp)

    # def __set_color(self, topic: Topic, payload: Dict[str, str]):
    #     light = self.__get_abstract_force(topic)
    #     color = Color(payload["color"])
    #     light.set_color_temp(color)
    #     self.__refresh(topic)

    def __rename_device(self, topic: Topic, payload: Dict[str, str]):
        # ToDo
        raise NotImplementedError
        # pay = Payload.rename(topic.without_base, payload["new_name"])
        # target = Topic.for_bridge(["request", "device"], "rename")
        # self.__client.publish(target.string, payload=pay)

    def __refresh(self, topic: Topic):
        Log.api.debug("Refreshing device with topic %s.", topic)
        if topic.category == TopicCategory.Home:
            return self.__refresh_home()
        target = get_abstract_force(topic, home=self.__home)
        for light in target.flatten_lights():
            self.__refresh_single(light)

    def __refresh_home(self):
        for room in self.__home.rooms:
            self.__refresh(room.group.topic)

    def __refresh_single(self, light: lighting.Abstract):
        target = get_configured_state(self.__home, light)
        light.realize_state(self.__client, target)

    def __query_state(self, topic: Topic):
        payload = Payload().state(None).finalize()
        Log.api.debug("Querying state of %s, which is %s.", topic, payload)
        self.__client.publish(topic.as_get(), payload=payload)

    def __update_state(self, topic: Topic, payload: Dict[str, str]):
        light = get_abstract(topic, home=self.__home)
        if light is not None:
            return self.__update_light_state(light, payload)
        sensor = get_sensor(topic, home=self.__home)
        if sensor is not None:
            return self.__update_sensor_state(sensor, payload)
        raise HomeBaseError.DeviceNotFound

    def __update_light_state(self, target: lighting.Collection, payload: Dict[str, str]):
        if not isinstance(target, lighting.Concrete):
            raise HomeBaseError.InvalidPhysicalQuery
        desired = lighting.State.read_light_state(payload)
        actual = get_configured_state(self.__home, target)
        # TODO
        # target.accommodate_state(actual=actual, desired=desired)

    def __update_sensor_state(self, target: Sensor, payload: Dict[str, str]):
        for key in payload:
            quant = Payload.sensor_quant_mapping().get(key)
            if quant is None:
                continue
            try:
                val = float(payload[key])
                target.update_state(quant, val)
            except ValueError as exc:
                Log.api.warning("Invalid quantity for sensor update: Not a float. %s", payload[key])
                raise HomeBaseError.InvalidPhysicalQuantity from exc
