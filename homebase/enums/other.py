"Collecting enums."

from enum import Enum, auto
from typing import Optional


class TopicCommand(Enum):
    "Different Commands"
    GET = "get"
    SET = "set"

    @staticmethod
    def from_str(val: str) -> Optional['TopicCommand']:
        "Creates a topic command from a string if possible."
        if val not in TopicCommand._member_names_:  # pylint: disable=no-member
            return None
        return TopicCommand[val]


class QoS(Enum):
    "All quality of service specifications"
    ONLY_ONCE = 2
    AT_LEAST_ONCE = 1
    ONCE = 0


# pylint: disable=invalid-name
class ApiCommand(Enum):
    "An API Command."
    Toggle                  = auto()
    TurnOn                  = auto()
    TurnOff                 = auto()
    DimUp                   = auto()
    DimDown                 = auto()
    StartDimUp              = auto()
    StartDimDown            = auto()
    StopDimming             = auto()
    EnableDynamicDimming    = auto()
    DisableDynamicDimming   = auto()
    EnableDynamicColor      = auto()
    DisableDynamicColor     = auto()
    SetBrightness           = auto()
    SetWhiteTemp            = auto()
    SetColor                = auto()
    Rename                  = auto()
    Refresh                 = auto()
    QueryPhysicalState      = auto()
    UpdateVirtualState      = auto()

    @staticmethod
    def from_str(val: str) -> Optional['ApiCommand']:
        "Creates a command from a string if possible."
        if val not in ApiCommand._member_names_:  # pylint: disable=no-member
            return None
        return ApiCommand[val]


# pylint: disable=invalid-name
class ApiQuery(Enum):
    "A query retrieved over the Api"
    Structure  = 1
    LightState = 2

    @staticmethod
    def from_str(val: str) -> Optional['ApiQuery']:
        "Creates a command from a string if possible."
        if val not in ApiQuery._member_names_:  # pylint: disable=no-member
            return None
        return ApiQuery[val]


# pylint: disable=invalid-name
class QDataKind(Enum):
    "Kind of a queue data"
    Status = 2
    ApiAction = 3
    ApiQuery = 4


# pylint: disable=invalid-name
class TopicTarget(str, Enum):
    "Entities addressable via a topic."
    Device = "Device"
    Remote = "Remote"
    Home   = "Home"
    Room   = "Room"
    Group  = "Group"
    Bridge = "bridge"

    @staticmethod
    def from_str(val: str) -> Optional['TopicTarget']:
        "Creates a topic target from a string if possible."
        if val not in set(item.value for item in TopicTarget):
            return None
        return TopicTarget(val)
