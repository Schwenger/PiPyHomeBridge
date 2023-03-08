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

# pylint: disable=too-few-public-methods
class ApiResponder:
    "Responds to API queries."
    def __init__(self, home: Home, _client: mqtt.Client):
        self.__home = home
        # self.__client = client  # Send request to client for current state

    def respond(self, topic: Topic, query: ApiQuery, channel: Queue):
        "Executes an API query."
        if   query == ApiQuery.Structure:
            response = self.__respond_structure()
        elif query == ApiQuery.LightState:
            response = self.__respond_light(topic)
        else:
            raise ValueError("Unknown ApiQuery: " + str(query))
        data = Payload.cleanse(Payload.as_json(response))
        channel.put(data)

    def __respond_structure(self) -> Dict:
        rooms = []
        for room in self.__home.rooms:
            remotes = []
            for remote in room.remotes:
                remotes.append({
                    "name": remote.name,
                    "id": remote.ident,
                    "topic": remote.topic.string,
                    "actions": list(map(lambda a: a.string, remote.actions()))
                })
            rooms.append({
                "name":     room.name,
                "lights":   self.__compile_group_structure(room.lights),
                "remotes":  remotes,
            })
        return {
            "rooms": rooms,
        }

    def __compile_group_structure(self, group: LightGroup) -> Dict:
        single = list(map(
            lambda l: {
                "name": l.name,
                "id": l.ident,
                "topic": l.topic.string,
                "kind": l.kind.value,
                "dimmable": l.is_dimmable(),
                "color": l.is_color(),
            },
            group.single_lights
        ))
        return {
            "name": group.name,
            "singleLights": single,
            "groups": list(map(self.__compile_group_structure, group.groups)),
        }

    def __respond_light(self, topic) -> Dict:
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
