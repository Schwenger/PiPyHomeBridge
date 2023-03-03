"Data to be put into the queue."

from typing import Optional
from topic import Topic
from light import LightState
from enums import QDataKind, ApiCommand

class QData:
    "Data to be stored in the queue."
    def __init__(
        self,
        kind:    QDataKind,
        topic:   Optional[Topic]        = None,
        state:   Optional[LightState]   = None,
        command: Optional[ApiCommand]   = None,
        payload: Optional[str]          = None,
    ):
        self.kind: QDataKind                = kind
        self.topic: Optional[Topic]         = topic
        self.state: Optional[LightState]    = state
        self.command: Optional[ApiCommand]  = command
        self.payload: Optional[str]         = payload

    @staticmethod
    def refresh() -> 'QData':
        "Refresh lights based on dynamic settings"
        return QData(kind=QDataKind.Refresh)

    @staticmethod
    def api_command(topic: Topic, command: ApiCommand, payload: Optional[str]) -> 'QData':
        "Creates an entity of queue data for the given api command."
        return QData(kind=QDataKind.ApiAction, topic=topic, command=command, payload=payload)
