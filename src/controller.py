"Example for contorling tradfri devices over python."

import time
import threading
import json
from typing import Dict
from queue import Queue
from paho.mqtt import client as mqtt
from rooms import Home
from remote import Remote
from payload import QoS
import queue_data as QData
import log

# config  = base.load_config()
# ip      = config['mosquitto']['ip']
# port    = int(config['mosquitto']['port'])
IP   = "192.168.178.34"
PORT = 1883

class Controller:
    "Controls a home"
    def __init__(self):
        self.client = self.init_client()
        self.queue = Queue()
        self.home = Home()
        self.remote_lookup: Dict[str, Remote] = self.init_remote_lookup()
        self.subscribe_to_remotes()
        for room in self.home.rooms:
            room.lights_off(self.client)
        self.client.on_message = self.handle_message

    def init_remote_lookup(self) -> Dict[str, Remote]:
        "Initializes the lookup for remotes based on topic."
        remote_lookup: Dict[str, Remote] = {}
        for remote in self.home.remotes():
            remote_lookup[remote.topic()] = remote
        return remote_lookup

    def subscribe_to_remotes(self):
        "Subscribes to messages from all remotes"
        for remote in self.home.remotes():
            (_result, _mid) = self.client.subscribe(remote.topic(), QoS.AT_LEAST_ONCE.value)

    def init_client(self) -> mqtt.Client:
        "Initializes a client."
        res = mqtt.Client("Mac")
        res.connect(IP, PORT, 60)
        return res

    def handle_message(self, _client, _userdata, message):
        "Handles the reception of a message"
        topic = message.topic
        payload = json.loads(message.payload.decode("utf-8"))
        if "action" not in payload:
            log.alert("Message without action found!")
            log.alert(payload)
            return
        remote = self.remote_lookup[topic]
        if remote is not None:
            self.queue.put(QData.remote_message(remote, payload["action"]))
            return
        log.alert("Could not find remote for " + topic)
        log.alert(payload)
        # raise ValueError(payload)

    def refresh_periodically(self, msg_q):
        "Periodically issues a refresh command through the queue."
        msg_q.put(QData.REFRESH)
        time.sleep(15*60)

    def process(self, qdata):
        "Processes data found in the queue"
        if qdata["kind"] == QData.KIND_REFRESH:
            for room in self.home.rooms:
                room.refresh_lights(self.client)
        elif qdata["kind"] == QData.KIND_REMOTE_MESSAGE:
            remote = qdata["remote"]
            action = qdata["action"]
            remote.execute_command(self.client, action)
        else:
            raise ValueError(qdata["kind"])

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
