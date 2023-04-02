"""
The logic for executing API commands
"""

from queue import Queue
from typing import Dict

import lighting
from api.api_common import get_configured_state
from comm import Payload, Topic
from common import Log
from enums import ApiQuery, SensorQuantity
from home import Home, Room
from homebaseerror import HomeBaseError
from paho.mqtt import client as mqtt
from remote import Remote
from sensor import Sensor


class Responder:
    "Responds to API queries."
    def __init__(self, home: Home, response: Queue, _client: mqtt.Client):
        self.__home = home
        self.__response = response


    def respond(self, topic: Topic, query: ApiQuery):
        "Executes an API query."
        response = {
            ApiQuery.Structure:   self.__respond_structure,
            ApiQuery.LightState:  lambda: self.__respond_light(topic),
            ApiQuery.SensorState: lambda: self.__respond_sensor(topic),
        }[query]()
        data = Payload.prep_for_sending(response)
        self.__response.put(data)


    def __respond_structure(self) -> Dict:
        return {
            "rooms": list(map(self.__compile_room, self.__home.rooms))
        }

    def __compile_room(self, room: Room) -> Dict:
        return {
            "name":     room.name,
            "icon":     room.icon,
            "lights":   self.__compile_group(room.group),
            "remotes":  list(map(self.__compile_remote, room.remotes)),
            "sensors":  list(map(self.__compile_sensor, room.sensors)),
        }

    def __compile_remote(self, remote: Remote) -> Dict:
        return {
            "name":   remote.name,
            "id":     remote.ident,
            "icon":   remote.icon,
            "topic":  remote.topic.string,
            "model":  remote.model.value,
            "actions": list(map(lambda a: a.string, remote.actions())),
        }

    def __compile_sensor(self, sensor: Sensor) -> Dict:
        return {
            "name":   sensor.name,
            "id":     sensor.ident,
            "icon":   sensor.icon,
            "topic":  sensor.topic.string,
            "model":  sensor.model.value,
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
            "icon":     light.icon,
            "topic":    light.topic.string,
            "model":    light.model.value,
        }

    def __respond_light(self, topic) -> Dict:
        Log.api.debug(topic)
        if topic is None:
            raise HomeBaseError.Unreachable
        light = self.__home.find_light(topic=topic)
        if light is None:
            raise HomeBaseError.DeviceNotFound
        state = get_configured_state(self.__home, light)
        return self.__respond_light_state(state)

    def __respond_light_state(self, state: lighting.State) -> Dict:
        return {
            "brightness": state.brightness,
            "hexColor": state.color.get_hex_l(),
            "toggledOn": state.toggled_on,
        }

    def __respond_sensor(self, topic) -> Dict:
        if topic is None:
            raise HomeBaseError.Unreachable
        sensor = self.__home.find_sensor(topic=topic)
        if sensor is None:
            raise HomeBaseError.DeviceNotFound
        return self.__respond_sensor_state(sensor.state)

    def __respond_sensor_state(self, state: Dict[SensorQuantity, float]) -> Dict[str, float]:
        res = { }
        for key in state:
            res[key.value] = state[key]
        return res
