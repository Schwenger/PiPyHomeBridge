"Bla"

from queue import Empty, Queue

from api.command import ApiExec
from api.query import ApiResponder
from comm.enums import QDataKind
from comm.queue_data import QData
from home.home import Home, HomeBaseError
from paho.mqtt import client as mqtt
from worker import Worker

import log


class Api(Worker):
    "Contains API logic."

    def __init__(self, request_q: Queue, response_q: Queue, home: Home, client: mqtt.Client):
        self.request_q  = request_q
        self.response_q = response_q
        self.exec       = ApiExec(home, client)
        self.responder  = ApiResponder(home, response_q, client)

    def run(self):
        while True:
            try:
                qdata: QData = self.request_q.get(block=True, timeout=60 * 15)
            except Empty:
                log.info("Controller: Heartbeat.")
                continue
            log.qdata(f"""
                Command: {qdata.command},
                Query: {qdata.query},
                Kind: {qdata.kind},
                Topic: {qdata.topic}
                """)
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
