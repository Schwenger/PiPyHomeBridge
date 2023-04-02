"Bla"

from queue import Queue

from api.command import Exec
from api.query import Responder
from comm import QData
from enums import QDataKind
from home import Home
from homebaseerror import HomeBaseError
from paho.mqtt import client as mqtt
from worker import Worker


class Api(Worker):
    "Contains API logic."

    def __init__(self, request_q: Queue, response_q: Queue, home: Home, client: mqtt.Client):
        self.request_q  = request_q
        self.response_q = response_q
        self.exec       = Exec(home, client)
        self.responder  = Responder(home, response_q, client)

    def _run(self):
        while True:
            qdata: QData = self.request_q.get(block=True)
            self.__process(qdata)

    def __process(self, qdata: QData):
        "Processes data found in the queue"
        if qdata.kind == QDataKind.ApiAction:
            self.__handle_api_action(qdata)
        elif qdata.kind == QDataKind.Status:
            raise ValueError("Status updates not supported, yet.")
        elif qdata.kind == QDataKind.ApiQuery:
            self.__handle_query(qdata)
        else:
            raise ValueError("Unknown QDataKind: " + str(qdata.kind))

    def __handle_api_action(self, qdata: QData):
        topic = qdata.topic
        cmd = qdata.command
        if qdata.kind != QDataKind.ApiAction or topic is None or cmd is None:
            raise HomeBaseError.Unreachable
        self.exec.exec(topic, cmd, qdata.payload)

    def __handle_query(self, qdata: QData):
        topic = qdata.topic
        query = qdata.query
        is_query = qdata.kind is QDataKind.ApiQuery
        if not is_query or topic is None or query is None:
            raise HomeBaseError.Unreachable
        self.responder.respond(topic, query)
