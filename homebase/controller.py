"Example for contorling tradfri devices over python."

import json
import logging
import time
from queue import Queue

import common
from enums import QoS, TopicCategory, ApiCommand, DeviceKind
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
        port = int(common.config["mosquitto"]["port"])
        self.client = self.__init_client(ip, port)
        self.queue  = queue
        self.home   = home
        self.client.on_disconnect = Controller.__on_disconnect_wrapper(ip, port)
        self.client.on_message    = self.__handle_message
        self.__subscribe_to_all()
        self.__query_states()

    @staticmethod
    def __on_disconnect_wrapper(ip, port):
        return lambda client, user, rc: Controller.__on_disconnect(ip, port, client, user, rc)

    @staticmethod
    def __on_disconnect(ip, port, client: mqtt.Client, _userdata,  _rc):
        logging.error("Client disconnected.")
        client.connect(host=ip, port=port, keepalive=360)

    def _run(self):
        "Retrieves message from the queue and processes it."
        self.client.loop_start()

    def __handle_message(self, _client, _userdata, message: mqtt.MQTTMessage):
        "Handles the reception of a message"
        logging.info("MQTT: Message received.")
        sender = Topic.from_str(message.topic)
        if len(message.payload) == 0:
            return
        logging.debug("MQTT: Message from %s received.", sender)
        data = json.loads(message.payload.decode("utf-8"))
        print(f"Devicekind is {sender.device_kind}")
        print(data)
        if sender.category is TopicCategory.Bridge:
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
        elif "state" in data or sender.device_kind == DeviceKind.Sensor.value:
            logging.debug("Received update for Sensor: %s", data)
            qdata = QData.api_command(sender, ApiCommand.UpdateState, payload=data)
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
        self.__subscribe_to_sensors()
        self.__subscribe_to_bridge()

    def __subscribe_to_bridge(self):
        self.client.subscribe(Topic.for_bridge().string, QoS.AT_LEAST_ONCE.value)

    def __subscribe_to_remotes(self):
        "Subscribes to messages from all remotes"
        for remote in self.home.remotes():
            self.client.subscribe(remote.topic.string, QoS.AT_LEAST_ONCE.value)
            logging.debug("Subscribing to %s", remote.topic)

    def __subscribe_to_sensors(self):
        "Subscribes to messages from all remotes"
        for sensor in self.home.sensors():
            self.client.subscribe(sensor.topic.string, QoS.AT_LEAST_ONCE.value)
            logging.debug("Subscribing to %s", sensor.topic)

    def __subscribe_to_lights(self):
        "Subscribes to messages from all lights"
        for light in self.home.flatten_lights():
            self.client.subscribe(light.topic.string, QoS.AT_LEAST_ONCE.value)
            logging.debug("Subscribing to %s", light.topic)

    def __query_states(self):
        "Queries the physical states of all relevant devices supporting a query, i.e. lights."
        for light in self.home.flatten_lights():
            data = QData.api_command(light.topic, ApiCommand.QueryState, payload={ })
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
