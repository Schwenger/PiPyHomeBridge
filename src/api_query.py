"""
The logic for executing API commands
"""

from queue import Queue
from paho.mqtt import client as mqtt
from home import Home
from topic import Topic
import payload as Payload
from queue_data import ApiQuery
from enums import HomeBaseError

# pylint: disable=too-few-public-methods
class ApiResponder:
    "Responds to API queries."
    def __init__(self, home: Home, _client: mqtt.Client):
        self.__home = home
        # self.__client = client  # Send request to client for current state

    def respond(self, topic: Topic, query: ApiQuery, channel: Queue[str]):
        "Executes an API query."
        if   query == ApiQuery.Structure:
            response = self.__respond_structure()
        elif query == ApiQuery.LightState:
            response = self.__respond_light(topic)
        else:
            raise ValueError("Unknown ApiQuery: " + str(query))
        data = Payload.cleanse(Payload.as_json(response))
        channel.put(data)

    def __respond_structure(self):
        return self.__home.structure()

    def __respond_light(self, topic):
        if topic is None:
            raise HomeBaseError.Unreachable
        light = self.__home.find_light(topic=topic)
        if light is None:
            raise HomeBaseError.LightNotFound
        return {
            "brightness": light.state.brightness,
            "hexColor": str(light.state.color.get_hex_l()),
            "toggledOn": str(light.state.toggled_on)
        }
