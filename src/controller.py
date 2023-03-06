"Example for contorling tradfri devices over python."

import time
import json
from queue import Queue
from paho.mqtt import client as mqtt
from home import Home
from enums import QoS, ApiQuery, HomeBaseError
from topic import Topic
from queue_data import QData, QDataKind
from api import ApiExec
import payload
import common

config = common.config
IP   = common.config['mosquitto']['ip']
PORT = common.config['mosquitto']['port']

class Controller:
    "Controls a home"

    # pylint: disable=invalid-name
    def __init__(self, ip: str, port: int, queue: Queue):
        self.client = self.__init_client(ip, port)
        self.queue = queue
        self.home = Home()
        self.api = ApiExec(self.home, self.client)
        self.__subscribe_to_all()
        self.client.on_message = self.__handle_message

    def run(self):
        "Retrieves message from the queue and processes it."
        self.client.loop_start()
        self.queue.put(QData.refresh())
        while True:
            self.__process(self.queue.get(block=True))

    def refresh_periodically(self):
        "Periodically issues a refresh command through the queue."
        while True:
            self.queue.put(QData.refresh())
            time.sleep(15*60)

    def __handle_message(self, _client, _userdata, message: mqtt.MQTTMessage):
        "Handles the reception of a message"
        remote_topic = Topic.from_str(message.topic)
        data = json.loads(message.payload.decode("utf-8"))
        if "action" not in data:
            # Probably status update, can even come from a remote!
            return
        remote_target = self.home.remote_action(remote_topic, data["action"])
        if remote_target is None:
            raise HomeBaseError.RemoteNotFound
        (cmd, target_topic) = remote_target
        qdata = QData.api_command(target_topic, cmd, payload={ })
        self.queue.put(qdata)

    def __process(self, qdata: QData):
        "Processes data found in the queue"
        if qdata.kind == QDataKind.Refresh:
            self.home.refresh_lights(self.client)
        elif qdata.kind == QDataKind.ApiAction:
            self.__handle_api_action(qdata)
        elif qdata.kind == QDataKind.Status:
            raise ValueError("Status updates not supported, yet.")
        elif qdata.kind == QDataKind.ApiQuery:
            self.__handle_query(qdata)
        else:
            raise ValueError("Unknown QDataKind: " + qdata.kind)

    def __handle_api_action(self, qdata: QData):
        topic = qdata.topic
        cmd = qdata.command
        if qdata.kind != QDataKind.ApiAction or topic is None or cmd is None:
            raise HomeBaseError.Unreachable
        self.api.exec(topic, cmd, qdata.payload)

    def __handle_query(self, qdata: QData):
        if qdata.kind != QDataKind.ApiQuery or qdata.response is None:
            raise HomeBaseError.Unreachable
        if qdata.query == ApiQuery.Structure:
            structure = self.home.structure()
            data = payload.cleanse(payload.as_json(structure))
            qdata.response.put(data)
        elif qdata.query == ApiQuery.LightState:
            if qdata.topic is None:
                raise HomeBaseError.Unreachable
            light = self.home.find_light(topic=qdata.topic)
            if light is None:
                raise HomeBaseError.LightNotFound
            state = {
                "brightness": light.state.brightness,
                "hexColor": str(light.state.color.get_hex_l())
            }
            data = payload.cleanse(payload.as_json(state))
            qdata.response.put(data)
        else:
            raise ValueError("Unknown ApiQuery: " + str(qdata.query))

    # pylint: disable=invalid-name
    def __init_client(self, ip: str, port: int) -> mqtt.Client:
        "Initializes a client."
        res = mqtt.Client(common.CLIENT_NAME)
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
            print(f"Subscribing to {remote.topic.string}")
            self.client.subscribe(remote.topic.string, QoS.AT_LEAST_ONCE.value)

    def __subscribe_to_lights(self):
        "Subscribes to messages from all lights"
        for light in self.home.flatten_lights():
            # This currently works because there are no light groups, yet.
            # Fix by having a function return physical lights from a room/group/home
            self.client.subscribe(light.topic.string, QoS.AT_LEAST_ONCE.value)
