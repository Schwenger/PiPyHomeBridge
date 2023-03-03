"Data to be put into the queue."

from enum import Enum
from typing import Optional
from payload import Topic
from light import LightState

# pylint: disable=invalid-name
class ApiCommand(Enum):
    "An API Command."
    Toggle                  = 0
    TurnOn                  = 1
    TurnOff                 = 2
    DimUp                   = 3
    DimDown                 = 4
    StartDimUp              = 5
    StartDimdown            = 6
    StopDimming             = 7
    EnableDynamicDimming    = 8
    DisableDynamicDimming   = 9
    EnableDynamicColor      = 10
    DisableDynamicColor     = 11
    SetBrightness           = 12
    SetWhiteTemp            = 13
    SetColor                = 14
    Rename                  = 15

# pylint: disable=invalid-name
class QDataKind(Enum):
    "Kind of a queue data"
    Status = 2
    ApiAction = 3
    Refresh = 4

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
