"Example for contorling tradfri devices over python."

import time
from paho.mqtt import client as mqtt
# from common import base
from rooms import Home
from payload import QoS
from log import info

# config  = base.load_config()
# ip      = config['mosquitto']['ip']
# port    = int(config['mosquitto']['port'])
IP   = "192.168.178.34"
PORT = 1883

client = mqtt.Client("Mac")
client.connect(IP, PORT, 60)

home = Home()

for room in home.rooms:
    room.lights_off(client)
    room.lights_on(client)
    room.refresh_lights(client)

for remote in home.remotes():
    (result, mid) = client.subscribe(remote.topic(), QoS.AT_LEAST_ONCE.value)
    client.message_callback_add(remote.topic(), remote.on_message)

client.loop_start()

# orb = home.rooms[0].lights[3]
# client.loop_start()

while True:
    info("refreshing lights")
    home.refresh_lights(client)
    time.sleep(15*60)
