"Example for contorling tradfri devices over python."

import json
import logging
import time
from queue import Queue

import common
from enums import QoS, TopicTarget
from comm.queue_data import QData
from comm.topic import Topic
from home.home import Home
from homebaseerror import HomeBaseError
from paho.mqtt import client as mqtt
from worker import Worker

config = common.config
IP   = common.config['mosquitto']['ip']
PORT = common.config['mosquitto']['port']


class PatchedClient(mqtt.Client):
    "Patches the publish command to also log the request."
    def publish(self: mqtt.Client, topic, payload=None, qos=0, retain=False, properties=None):
        if payload is not None:
            logging.info("MQTT: Sending message to %s with payload %s.", topic, payload)
        super().publish(topic, payload, qos, retain, properties)


class Controller(Worker):
    "Controls a home"

    # pylint: disable=invalid-name
    def __init__(self, queue: Queue, home: Home):
        ip = common.config["mosquitto"]["ip"]
        port = common.config["mosquitto"]["port"]
        self.client = self.__init_client(ip, int(port))
        self.queue  = queue
        self.home   = home
        self.client.on_disconnect = Controller.__on_disconnect
        self.client.on_message    = self.__handle_message
        self.__subscribe_to_all()

    @staticmethod
    def __on_disconnect(_client, _userdata,  _rc):
        logging.error("Client disconnected.")

    def _run(self):
        "Retrieves message from the queue and processes it."
        self.client.loop_start()

    def __handle_message(self, _client, _userdata, message: mqtt.MQTTMessage):
        "Handles the reception of a message"
        remote_topic = Topic.from_str(message.topic)
        data = json.loads(message.payload.decode("utf-8"))
        if remote_topic.target is TopicTarget.Bridge:
            logging.info("Received a message with bridge event.")
            logging.info(str(remote_topic))
            logging.info(str(data))
        if "action" not in data:
            # Probably status update, can even come from a remote!
            return
        remote_target = self.home.remote_action(remote_topic, data["action"])
        if remote_target is None:
            raise HomeBaseError.RemoteNotFound
        (cmd, target_topic) = remote_target
        qdata = QData.api_command(target_topic, cmd, payload={ })
        self.queue.put(qdata)

    # pylint: disable=invalid-name
    def __init_client(self, ip: str, port: int) -> mqtt.Client:
        "Initializes a client."
        res = PatchedClient(common.CLIENT_NAME)
        res.connect(host=ip, port=port, keepalive=360)
        return res

    def __subscribe_to_all(self):
        self.__subscribe_to_lights()
        self.__subscribe_to_remotes()
        self.__subscribe_to_bridge()

    def __subscribe_to_bridge(self):
        self.client.subscribe("zigbee2mqtt/bridge/event", QoS.AT_LEAST_ONCE.value)

    def __subscribe_to_remotes(self):
        "Subscribes to messages from all remotes"
        for remote in self.home.remotes():
            self.client.subscribe(remote.topic.string, QoS.AT_LEAST_ONCE.value)

    def __subscribe_to_lights(self):
        "Subscribes to messages from all lights"
        for light in self.home.flatten_lights():
            # This currently works because there are no light groups, yet.
            # Fix by having a function return physical lights from a room/group/home
            self.client.subscribe(light.topic.string, QoS.AT_LEAST_ONCE.value)


class Refresher(Worker):
    "Periodically issues a refresh command on the queue."
    def __init__(self, queue: Queue):
        self.queue = queue

    def _run(self):
        "Periodically issues a refresh command through the queue."
        while True:
            self.queue.put(QData.refresh())
            time.sleep(15 * 60)
