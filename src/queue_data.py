"Data to be put into the queue."

from queue import Queue
from typing import Optional, Dict
from topic import Topic
from light import LightState
from enums import QDataKind, ApiCommand, ApiQuery

class QData:
    "Data to be stored in the queue."
    def __init__(
        self,
        kind:     QDataKind,
        payload:  Dict[str, str],
        topic:    Optional[Topic]      = None,
        state:    Optional[LightState] = None,
        command:  Optional[ApiCommand] = None,
        query:    Optional[ApiQuery]   = None,
        response: Optional[Queue[str]]      = None,
    ):
        self.kind:     QDataKind            = kind
        self.topic:    Optional[Topic]      = topic
        self.state:    Optional[LightState] = state
        self.command:  Optional[ApiCommand] = command
        self.query:    Optional[ApiQuery]   = query
        self.payload:  Dict[str, str]       = payload
        self.response: Optional[Queue[str]]      = response

    @staticmethod
    def refresh() -> 'QData':
        "Refresh lights based on dynamic settings"
        return QData(kind=QDataKind.Refresh, payload={})

    @staticmethod
    def api_command(topic: Topic, command: ApiCommand, payload: Dict[str, str]) -> 'QData':
        "Creates an entity of queue data for the given api command."
        return QData(
            kind=QDataKind.ApiAction,
            topic=topic,
            command=command,
            payload=payload
        )

    @staticmethod
    def api_query(topic: Topic, query: ApiQuery, response: Queue) -> 'QData':
        "Creates an API query."
        return QData(
            kind=QDataKind.ApiQuery,
            topic=topic,
            query=query,
            response=response,
            payload={}
        )
