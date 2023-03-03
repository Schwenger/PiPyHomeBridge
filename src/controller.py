"Example for contorling tradfri devices over python."

import time
import json
from queue import Queue
from paho.mqtt import client as mqtt
from rooms import Home
from payload import QoS, Topic
from queue_data import QData, QDataKind
from api import ApiExec
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
        while True:
            self.__process(self.queue.get(block=True))

    def refresh_periodically(self):
        "Periodically issues a refresh command through the queue."
        while True:
            self.queue.put(QData.refresh())
            time.sleep(15*60)

    def __handle_message(self, _client, _userdata, message: mqtt.MQTTMessage):
        "Handles the reception of a message"
        topic = Topic.from_str(message.topic)
        payload = json.loads(message.payload.decode("utf-8"))
        if topic.device == "Remote":
            print(f"@{topic.string}: {payload}")
        if "action" not in payload:
            # Probably status update, can even come from a remote!
            return
        cmd = self.home.remote_action(topic, payload["action"])
        assert cmd is not None
        qdata = QData.api_command(topic, cmd, None)
        self.queue.put(qdata)

    def __process(self, qdata:QData):
        "Processes data found in the queue"
        assert qdata is not None
        if qdata.kind == QDataKind.Refresh:
            self.home.refresh_lights(self.client)
        elif qdata.kind == QDataKind.ApiAction:
            self.__handle_api_action(qdata)
        elif qdata.kind == QDataKind.Status:
            ValueError("Status updates not supported, yet.")

    def __handle_api_action(self, qdata: QData):
        topic = qdata.topic
        assert topic is not None
        cmd = qdata.command
        assert cmd is not None
        self.api.exec(topic, cmd, qdata.payload)

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
            (_result, _mid) = self.client.subscribe(remote.topic.string, QoS.AT_LEAST_ONCE.value)

    def __subscribe_to_lights(self):
        "Subscribes to messages from all lights"
        for light in self.home.lights():
            (_result, _mid) = self.client.subscribe(light.topic.string, QoS.AT_LEAST_ONCE.value)
