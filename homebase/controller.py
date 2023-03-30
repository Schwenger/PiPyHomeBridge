"Example for contorling tradfri devices over python."

import json
import logging
import time
from queue import Queue

import common
from enums import QoS, TopicTarget, ApiCommand
from comm import QData, Topic
from home import Home
from homebaseerror import HomeBaseError
from paho.mqtt import client as mqtt
from worker import Worker

config = common.config
IP   = common.config['mosquitto']['ip']
PORT = common.config['mosquitto']['port']


class PatchedClient(mqtt.Client):
    "Patches the publish command to also log the request."
    def publish(self: mqtt.Client, topic, payload=None, qos=0, retain=False, properties=None):
        logging.info("MQTT: Sending message.")
        if payload is not None:
            logging.info("MQTT: Sending to %s: %s.", topic, payload)
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
        self.__query_physical_states()

    @staticmethod
    def __on_disconnect(_client, _userdata,  _rc):
        logging.error("Client disconnected.")

    def _run(self):
        "Retrieves message from the queue and processes it."
        self.client.loop_start()

    def __handle_message(self, _client, _userdata, message: mqtt.MQTTMessage):
        "Handles the reception of a message"
        logging.info("MQTT: Message received.")
        sender = Topic.from_str(message.topic)
        logging.debug("MQTT: Message from %s received.", sender)
        data = json.loads(message.payload.decode("utf-8"))
        if sender.target is TopicTarget.Bridge:
            logging.debug("Received a message with bridge event.")
            logging.debug(str(sender))
            logging.debug(str(data))
        if "action" in data:
            remote_target = self.home.remote_action(sender, data["action"])
            if remote_target is None:
                raise HomeBaseError.RemoteNotFound
            (cmd, target_topic) = remote_target
            qdata = QData.api_command(target_topic, cmd, payload={ })
            self.queue.put(qdata)
        if "state" in data:
            qdata = QData.api_command(sender, ApiCommand.UpdateVirtualState, payload=data)
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

    def __query_physical_states(self):
        "Queries the physical states of all lights"
        for light in self.home.flatten_lights():
            data = QData.api_command(light.topic, ApiCommand.QueryPhysicalState, payload={ })
            self.queue.put(data)


class Refresher(Worker):
    "Periodically issues a refresh command on the queue."
    def __init__(self, queue: Queue):
        self.queue = queue

    def _run(self):
        "Periodically issues a refresh command through the queue."
        while True:
            self.queue.put(QData.refresh())
            time.sleep(15 * 60)
