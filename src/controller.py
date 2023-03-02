"Example for contorling tradfri devices over python."

import time
import threading
import json
from typing import List, Optional
from queue import Queue
from paho.mqtt import client as mqtt
from rooms import Home, Room
from remote import Remote
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

    def route_message(self, topic: Topic, payload):
        "Routes a message to the addressee identified by the topic."
        res = self.home.route_message(self.client, topic, payload)
        assert res == RoutingResult.ACCEPT

    def find_light(self, topic: Topic) -> Optional[Light]:
        "Finds the device with the given topic"
        return self.home.find_light(topic)

    def find_remote(self, topic: Topic) -> Optional[Remote]:
        "Finds the device with the given topic"
        return self.home.find_remote(topic)

    def handle_message(self, _client, _userdata, message: mqtt.MQTTMessage):
        "Handles the reception of a message"
        try:
            topic = Topic.from_str(message.topic)
            payload = json.loads(message.payload.decode("utf-8"))
            if topic.physical_kind == "Remote":
                print(f"@{topic.str}: {payload}")
            self.queue.put(QData.addressed(topic, payload))
        except Exception:
            return

    def refresh_periodically(self, msg_q):
        "Periodically issues a refresh command through the queue."
        msg_q.put(QData.REFRESH)
        time.sleep(15*60)

    def process(self, qdata):
        "Processes data found in the queue"
        try:
            if qdata["kind"] == QData.Kind.REFRESH:
                for room in self.home.rooms:
                    room.refresh_lights(self.client)
            elif qdata["kind"] == QData.Kind.ADDRESSED:
                topic = qdata["topic"]
                data  = qdata["data"]
                self.route_message(topic, data)
            elif qdata["kind"] == QData.Kind.API:
                cmd = qdata["cmd"]
                target = qdata["target"]
                if cmd == QData.Cmd.QUERY:
                    light = self.find_light(target)
                    if light is not None:
                        light.query_state(self.client)
        except Exception:
            return

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
