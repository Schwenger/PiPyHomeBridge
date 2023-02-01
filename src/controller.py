"Example for contorling tradfri devices over python."

import time
import threading
import json
from typing import Dict, Optional
from queue import Queue
from paho.mqtt import client as mqtt
from rooms import Home
from remote import Remote
from payload import QoS
import queue_data as QData

# config  = base.load_config()
# ip      = config['mosquitto']['ip']
# port    = int(config['mosquitto']['port'])
IP   = "192.168.178.34"
PORT = 1883

client = mqtt.Client("Mac")
client.connect(IP, PORT, 60)

queue = Queue()

home = Home()

for room in home.rooms:
    room.lights_off(client)

remote_lookup: Dict[str, Remote] = {}

for remote in home.remotes():
    (result, mid) = client.subscribe(remote.topic(), QoS.AT_LEAST_ONCE.value)
    remote_lookup[remote.topic()] = remote

def find_remote(topic) -> Optional[Remote]:
    "Returns the remote for the given topic if any."
    return remote_lookup[topic]

def handle_message(_client, _userdata, message):
    "Handles the reception of a message"
    topic = message.topic
    payload = json.loads(message.payload.decode("utf-8"))
    remote = find_remote(topic)
    if remote is not None:
        queue.put(QData.remote_message(remote, payload["action"]))
        return
    raise ValueError(payload)

client.on_message = handle_message

# orb = home.rooms[0].lights[3]
# client.loop_start()

def refresh_periodically(msg_q):
    "Periodically issues a refresh command through the queue."
    msg_q.put(QData.REFRESH)
    time.sleep(15*60)

thread = threading.Thread(target=refresh_periodically, args=(queue,))
thread.start()

def process(qdata):
    "Processes data found in the queue"
    if qdata["kind"] == QData.KIND_REFRESH:
        for room in home.rooms:
            room.refresh_lights(client)
    elif qdata["kind"] == QData.KIND_REMOTE_MESSAGE:
        remote = qdata["remote"]
        action = qdata["action"]
        remote.execute_command(client, action)
    else:
        raise ValueError(qdata["kind"])

client.loop_start()
while True:
    process(queue.get(block=True))
client.loop_stop()
