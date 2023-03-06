"""
The logic for executing API commands
"""

from typing import Dict
from paho.mqtt import client as mqtt
from colour import Color
from light_group import AbstractLight #, LightGroup
from home import Home
from topic import Topic
import payload as Payload
from queue_data import ApiCommand
from enums import HomeBaseError

# pylint: disable=too-few-public-methods
class ApiExec:
    "Executes API command."
    def __init__(self, home: Home, client: mqtt.Client):
        self.__home = home
        self.__client = client

    def exec(self, topic: Topic, cmd: ApiCommand, payload: Dict[str, str]):
        "Executes the specifier API command."
        if   cmd == ApiCommand.Toggle:
            self.__toggle(topic)
        elif cmd == ApiCommand.TurnOn:
            self.__turn_on(topic)
        elif cmd == ApiCommand.TurnOff:
            self.__turn_off(topic)
        elif cmd == ApiCommand.DimUp:
            self.__dim_up(topic)
        elif cmd == ApiCommand.DimDown:
            self.__dim_down(topic)
        elif cmd == ApiCommand.StartDimUp:
            self.__start_dim_up(topic)
        elif cmd == ApiCommand.StartDimDown:
            self.__start_dim_down(topic)
        elif cmd == ApiCommand.StopDimming:
            self.__stop_dimming(topic)
        elif cmd == ApiCommand.EnableDynamicDimming:
            pass
        elif cmd == ApiCommand.DisableDynamicDimming:
            pass
        elif cmd == ApiCommand.EnableDynamicColor:
            pass
        elif cmd == ApiCommand.DisableDynamicColor:
            pass
        elif cmd == ApiCommand.SetBrightness:
            if payload is None:
                raise HomeBaseError.PayloadNotFound
            self.__set_brightness(topic, payload)
        elif cmd == ApiCommand.SetWhiteTemp:
            if payload is None:
                raise HomeBaseError.PayloadNotFound
            self.__set_white_temp(topic, payload)
        elif cmd == ApiCommand.SetColor:
            if payload is None:
                raise HomeBaseError.PayloadNotFound
            self.__set_color(topic, payload)
        elif cmd == ApiCommand.Rename:
            if payload is None:
                raise HomeBaseError.PayloadNotFound
            self.__rename_device(topic, payload)

    def __get_target(self, topic: Topic) -> AbstractLight:
        light = self.__home.find_light(topic)
        if light is not None:
            return light
        room = self.__home.room_by_name(topic.name)
        if room is None:
            raise HomeBaseError.RoomNotFound
        return room.lights

    def __toggle(self, topic: Topic):
        self.__get_target(topic).toggle(self.__client)

    def __turn_on(self, topic: Topic):
        self.__get_target(topic).turn_on(self.__client)

    def __turn_off(self, topic: Topic):
        self.__get_target(topic).turn_off(self.__client)

    def __dim_up(self, topic: Topic):
        self.__get_target(topic).dim_up(self.__client)

    def __dim_down(self, topic: Topic):
        self.__get_target(topic).dim_down(self.__client)

    def __start_dim_up(self, topic: Topic):
        self.__get_target(topic).start_dim_up(self.__client)

    def __start_dim_down(self, topic: Topic):
        self.__get_target(topic).start_dim_down(self.__client)

    def __stop_dimming(self, topic: Topic):
        self.__get_target(topic).stop_dim(self.__client)

    def __set_brightness(self, topic: Topic, payload: Dict[str, str]):
        light = self.__get_target(topic)
        brightness = float(payload["brightness"])
        light.set_brightness(self.__client, brightness)

    def __set_white_temp(self, topic: Topic, payload: Dict[str, str]):
        light = self.__get_target(topic)
        white_temp = float(payload["white"])
        light.set_white_temp(self.__client, white_temp)

    def __set_color(self, topic: Topic, payload: Dict[str, str]):
        light = self.__get_target(topic)
        color = Color(payload["color"])
        light.set_color_temp(self.__client, color)

    def __rename_device(self, topic: Topic, payload: Dict[str, str]):
        pay = Payload.rename(topic.without_base, payload["new_name"])
        target = "zigbee2mqtt/bridge/request/device/rename"
        self.__client.publish(target, payload=pay)
