"""
The logic for executing API commands
"""

import logging
from queue import Queue
from typing import Dict

import lighting
from comm.payload import Payload
from comm.queue_data import ApiQuery
from comm.topic import Topic
from home.device import Device
from home.home import Home
from homebaseerror import HomeBaseError
from paho.mqtt import client as mqtt


class ApiResponder:
    "Responds to API queries."
    def __init__(self, home: Home, response: Queue, _client: mqtt.Client):
        self.__home = home
        self.__response = response
        # self.__client = client  # Send request to client for current state

    def respond(self, topic: Topic, query: ApiQuery):
        "Executes an API query."
        logging.debug("ApiQuery: respond")
        if query == ApiQuery.Structure:
            response = self.__respond_structure()
        elif query == ApiQuery.LightState:
            response = self.__respond_light(topic)
        else:
            raise ValueError("Unknown ApiQuery: " + str(query))
        data = Payload.prep_for_sending(response)
        self.__response.put(data)

    def __respond_structure(self) -> Dict:
        logging.debug("ApiQuery: __respond_structure")
        rooms = []
        for room in self.__home.rooms:
            remotes = []
            for remote in room.remotes:
                res = self.__respond_device(remote)
                res["actions"] = list(map(lambda a: a.string, remote.actions()))
                remotes.append(res)
            rooms.append({
                "name":     room.name,
                "lights":   self.__compile_group_structure(room.group),
                "remotes":  remotes,
            })
        return {
            "rooms": rooms,
        }

    def __compile_group_structure(self, group: lighting.Group) -> Dict:
        logging.debug("ApiQuery: __compile_group_structure")
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
        logging.debug("ApiQuery: __respond_device")
        return {
            "name":   device.name,
            "id":     device.ident,
            "topic":  device.topic.string,
            "model":  device.model.value,
        }

    def __respond_light(self, topic) -> Dict:
        logging.debug("ApiQuery: __respond_light")
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
