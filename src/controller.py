"Example for contorling tradfri devices over python."

import time
import json
from queue import Queue
from paho.mqtt import client as mqtt
from home import Home
from enums import QoS, HomeBaseError
from topic import Topic
from queue_data import QData, QDataKind
from api_command import ApiExec
from api_query import ApiResponder
import common
from log import alert

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
        self.executer = ApiExec(self.home, self.client)
        self.responder = ApiResponder(self.home, self.client)
        self.__subscribe_to_all()
        self.client.on_message = self.__handle_message

    def run(self):
        "Retrieves message from the queue and processes it."
        self.client.loop_start()
        while True:
            try:
                qdata: QData = self.queue.get(block=True)
                self.__process(qdata)
            except HomeBaseError as e:
                if common.config["crash_on_error"]:
                    raise e
                alert(str(e))

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
        self.executer.exec(topic, cmd, qdata.payload)

    def __handle_query(self, qdata: QData):
        topic = qdata.topic
        query = qdata.query
        is_query = qdata.kind is QDataKind.ApiQuery
        if not is_query or topic is None or query is None or qdata.response is None:
            raise HomeBaseError.Unreachable
        self.responder.respond(topic, query, qdata.response)

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
            self.client.subscribe(remote.topic.string, QoS.AT_LEAST_ONCE.value)

    def __subscribe_to_lights(self):
        "Subscribes to messages from all lights"
        for light in self.home.flatten_lights():
            # This currently works because there are no light groups, yet.
            # Fix by having a function return physical lights from a room/group/home
            self.client.subscribe(light.topic.string, QoS.AT_LEAST_ONCE.value)
