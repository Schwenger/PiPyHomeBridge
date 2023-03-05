"""
The logic for executing API commands
"""

from typing import Optional
from paho.mqtt import client as mqtt
# from colour import Color
from light_group import AbstractLight #, LightGroup
from home import Home
from topic import Topic
import payload as Payload
from queue_data import ApiCommand

# pylint: disable=too-few-public-methods
class ApiExec:
    "Executes API command."
    def __init__(self, home: Home, client: mqtt.Client):
        self.__home = home
        self.__client = client

    def exec(self, topic: Topic, cmd: ApiCommand, payload: Optional[str]):
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
            pass
            # assert payload is not None
            # self.__set_brightness(topic, payload)
        elif cmd == ApiCommand.SetWhiteTemp:
            pass
            # assert payload is not None
            # self.__set_white_temp(topic, payload)
        elif cmd == ApiCommand.SetColor:
            pass
            # assert payload is not None
            # self.__set_color(topic, payload)
        elif cmd == ApiCommand.Rename:
            assert payload is not None
            self.__rename_device(topic, payload)

    def __get_target(self, topic: Topic) -> AbstractLight:
        light = self.__home.find_light(topic)
        if light is not None:
            return light
        room = self.__home.room_by_name(topic.name)
        assert room is not None
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

    # def __set_brightness(self, topic: Topic, payload: str):
    #     lights = self.__get_target(topic)
    #     state = lights.state
    #     state.brightness = int(payload)
    #     lights.realize_state(self.__client, state)

    # def __set_white_temp(self, topic: Topic, payload: str):
    #     lights = self.__get_target(topic)
    #     state = lights.state
    #     state.white_temp = int(payload)
    #     lights.realize_state(self.__client, state)

    # def __set_color(self, topic: Topic, payload: str):
    #     lights = self.__get_target(topic)
    #     state = lights.state
    #     state.color = Color(payload)
    #     lights.realize_state(self.__client, state)

    def __rename_device(self, topic: Topic, payload: str):
        payload = Payload.rename(topic.without_base, payload)
        target = "zigbee2mqtt/bridge/request/device/rename"
        self.__client.publish(target, payload=payload)
