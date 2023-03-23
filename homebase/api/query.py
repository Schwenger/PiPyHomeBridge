"""
The logic for executing API commands
"""

import logging
from queue import Queue
from typing import Dict

import lighting
from comm.payload import Payload
from comm.topic import Topic
from enums import ApiQuery
from home.home import Home
from home.remote import Remote
from home.room import Room
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
        if query == ApiQuery.Structure:
            response = self.__respond_structure()
        elif query == ApiQuery.LightState:
            response = self.__respond_light(topic)
        else:
            raise ValueError("Unknown ApiQuery: " + str(query))
        data = Payload.prep_for_sending(response)
        self.__response.put(data)

    def __respond_structure(self) -> Dict:
        return {
            "rooms": list(map(self.__compile_room, self.__home.rooms))
        }

    def __compile_room(self, room: Room) -> Dict:
        return {
            "name":     room.name,
            "lights":   self.__compile_group(room.group),
            "remotes":  list(map(self.__compile_remote, room.remotes)),
        }

    def __compile_remote(self, remote: Remote) -> Dict:
        return {
            "name":   remote.name,
            "id":     remote.ident,
            "topic":  remote.topic.string,
            "model":  remote.model.value,
            "actions": list(map(lambda a: a.string, remote.actions())),
        }

    def __compile_group(self, group: lighting.Group) -> Dict:
        return {
            "name": group.name,
            "singleLights": list(map(self.__compile_concrete, group.single_lights)),
            "groups": list(map(self.__compile_group, group.groups)),
        }

    def __compile_concrete(self, light: lighting.Concrete) -> Dict:
        return {
            "name":     light.name,
            "id":       light.ident,
            "topic":    light.topic.string,
            "model":    light.model.value,
            "dimmable": light.is_dimmable(),
            "color":    light.is_color(),
        }

    def __respond_light(self, topic) -> Dict:
        if topic is None:
            raise HomeBaseError.Unreachable
        light = self.__home.find_light(topic=topic)
        if light is None:
            raise HomeBaseError.LightNotFound
        return self.__respond_light_state(light.state)

    def __respond_light_state(self, state: lighting.State) -> Dict:
        return {
            "brightness": state.brightness,
            "hexColor": str(state.color.get_hex_l()),
            "toggledOn": str(state.toggled_on),
        }
