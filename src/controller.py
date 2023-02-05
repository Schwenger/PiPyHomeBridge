"Example for contorling tradfri devices over python."

import time
import threading
import json
from typing import List, Optional
from queue import Queue
from paho.mqtt import client as mqtt
from rooms import Home, Room
from lights import Light
from payload import QoS, Topic, RoutingResult
import queue_data as QData
import common

config = common.config
IP   = common.config['mosquitto']['ip']
PORT = common.config['mosquitto']['port']

class Controller:
    "Controls a home"
    def __init__(self):
        self.client = self.init_client()
        self.queue = Queue()
        self.home = Home()
        self.subscribe_to_remotes()
        self.subscribe_to_lights()
        for room in self.home.rooms:
            room.lights_off(self.client)
        self.client.on_message = self.handle_message

    def subscribe_to_remotes(self):
        "Subscribes to messages from all remotes"
        for remote in self.home.remotes():
            (_result, _mid) = self.client.subscribe(remote.topic(), QoS.AT_LEAST_ONCE.value)

    def subscribe_to_lights(self):
        "Subscribes to messages from all lights"
        for light in self.home.lights():
            (_result, _mid) = self.client.subscribe(light.topic(), QoS.AT_LEAST_ONCE.value)

    def init_client(self) -> mqtt.Client:
        "Initializes a client."
        res = mqtt.Client(common.CLIENT_NAME)
        res.connect(IP, PORT, 60)
        return res

    def lights(self) -> List[Light]:
        "Returns a list of all lights."
        res = []
        for room in self.home.rooms:
            res += room.lights
        return res

    def room_by_name(self, name: str) -> Optional[Room]:
        "Finds the room with the given name in the home."
        return next((room for room in self.home.rooms if room.name == name), None)

    def light_by_topic(self, topic: Topic) -> Optional[Light]:
        "Finds a light for a given topic"
        room = self.room_by_name(topic.room)
        if room is None:
            return None
        return room.light_by_name(topic.name)

    def route_message(self, topic: Topic, payload):
        "Routes a message to the addressee identified by the topic."
        res = self.home.route_message(self.client, topic, payload)
        assert res == RoutingResult.ACCEPT

    def handle_message(self, _client, _userdata, message: mqtt.MQTTMessage):
        "Handles the reception of a message"
        topic = Topic.from_str(message.topic)
        payload = json.loads(message.payload.decode("utf-8"))
        self.queue.put((topic, payload))

    def refresh_periodically(self, msg_q):
        "Periodically issues a refresh command through the queue."
        msg_q.put(QData.REFRESH)
        time.sleep(15*60)

    def process(self, data):
        "Processes data found in the queue"
        if data == QData.REFRESH:
            for room in self.home.rooms:
                room.refresh_lights(self.client)
            return
        (topic, payload) = data
        self.route_message(topic, payload)

    def loop(self):
        "Retrieves message from the queue and processes it."
        self.process(self.queue.get(block=True))

if __name__ == "__main__":
    controller = Controller()
    thread = threading.Thread(target=controller.refresh_periodically, args=(controller.queue,))
    thread.start()

    controller.client.loop_start()
    while True:
        controller.loop()
