"""
The logic for executing API commands
"""

from typing import Optional
from paho.mqtt import client as mqtt
from colour import Color
from home import Home
from light_group import LightGroup
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
        match cmd:
            case ApiCommand.Toggle:
                self.__toggle(topic)
            case ApiCommand.TurnOn:
                self.__turn_on(topic)
            case ApiCommand.TurnOff:
                self.__turn_off(topic)
            case ApiCommand.DimUp:
                self.__dim_up(topic)
            case ApiCommand.DimDown:
                self.__dim_down(topic)
            case ApiCommand.StartDimUp:
                self.__start_dim_up(topic)
            case ApiCommand.StartDimDown:
                self.__start_dim_down(topic)
            case ApiCommand.StopDimming:
                self.__stop_dimming(topic)
            case ApiCommand.EnableDynamicDimming:
                raise ValueError
            case ApiCommand.DisableDynamicDimming:
                raise ValueError
            case ApiCommand.EnableDynamicColor:
                raise ValueError
            case ApiCommand.DisableDynamicColor:
                raise ValueError
            case ApiCommand.SetBrightness:
                assert payload is not None
                self.__set_brightness(topic, payload)
            case ApiCommand.SetWhiteTemp:
                assert payload is not None
                self.__set_white_temp(topic, payload)
            case ApiCommand.SetColor:
                assert payload is not None
                self.__set_color(topic, payload)
            case ApiCommand.Rename:
                assert payload is not None
                self.__rename_device(topic, payload)

    def __get_target(self, _topic: Topic) -> LightGroup:
        room = self.__home.room_by_name("Living Room")
        assert room is not None
        return room.lights

    def __toggle(self, topic: Topic):
        self.__get_target(topic).toggle(self.__client)

    def __turn_on(self, topic: Topic):
        print("API: Turning on")
        self.__get_target(topic).turn_on(self.__client)

    def __turn_off(self, topic: Topic):
        print("API: Turning off")
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

    def __set_brightness(self, topic: Topic, payload: str):
        lights = self.__get_target(topic)
        state = lights.state
        state.brightness = int(payload)
        lights.realize_state(self.__client, state)

    def __set_white_temp(self, topic: Topic, payload: str):
        lights = self.__get_target(topic)
        state = lights.state
        state.white_temp = int(payload)
        lights.realize_state(self.__client, state)

    def __set_color(self, topic: Topic, payload: str):
        lights = self.__get_target(topic)
        state = lights.state
        state.color = Color(payload)
        lights.realize_state(self.__client, state)

    def __rename_device(self, topic: Topic, payload: str):
        payload = Payload.rename(topic.without_base, payload)
        target = "zigbee2mqtt/bridge/request/device/rename"
        self.__client.publish(target, payload=payload)
