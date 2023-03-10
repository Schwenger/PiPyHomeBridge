"""
The logic for executing API commands
"""

from queue import Queue
from typing import Dict
from paho.mqtt import client as mqtt
from home import Home
from topic import Topic
import payload as Payload
from queue_data import ApiQuery
from enums import HomeBaseError
from light_group import LightGroup
from device import Device
from log import trace

# pylint: disable=too-few-public-methods
class ApiResponder:
    "Responds to API queries."
    def __init__(self, home: Home, _client: mqtt.Client):
        self.__home = home
        # self.__client = client  # Send request to client for current state

    def respond(self, topic: Topic, query: ApiQuery, channel: Queue):
        "Executes an API query."
        trace("ApiQuery", "respond")
        if   query == ApiQuery.Structure:
            response = self.__respond_structure()
        elif query == ApiQuery.LightState:
            response = self.__respond_light(topic)
        else:
            raise ValueError("Unknown ApiQuery: " + str(query))
        data = Payload.cleanse(Payload.as_json(response))
        channel.put(data)

    def __respond_structure(self) -> Dict:
        trace("ApiQuery", "__respond_structure")
        rooms = []
        for room in self.__home.rooms:
            remotes = []
            for remote in room.remotes:
                res = self.__respond_device(remote)
                res["actions"] = list(map(lambda a: a.string, remote.actions()))
                remotes.append(res)
            rooms.append({
                "name":     room.name,
                "lights":   self.__compile_group_structure(room.lights),
                "remotes":  remotes,
            })
        return {
            "rooms": rooms,
        }

    def __compile_group_structure(self, group: LightGroup) -> Dict:
        trace("ApiQuery", "__compile_group_structure")
        singles = []
        for light in group.single_lights:
            res = self.__respond_device(light)
            res["dimmable"] = light.is_dimmable()
            res["color"] = light.is_color()
            singles.append(res)
        return {
            "name": group.name,
            "singleLights": singles,
            "groups": list(map(self.__compile_group_structure, group.groups)),
        }

    def __respond_device(self, device: Device) -> Dict:
        trace("ApiQuery", "__respond_device")
        return {
            "name":   device.name,
            "id":     device.ident,
            "topic":  device.topic.string,
            "model":  device.model.value,
        }

    def __respond_light(self, topic) -> Dict:
        trace("ApiQuery", "__respond_light")
        if topic is None:
            raise HomeBaseError.Unreachable
        light = self.__home.find_light(topic=topic)
        if light is None:
            raise HomeBaseError.LightNotFound
        return {
            "brightness": light.state.brightness,
            "hexColor": str(light.state.color.get_hex_l()),
            "toggledOn": str(light.state.toggled_on),
        }
