"Collecting enums."

from enum import Enum
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
    Toggle                  = 0
    TurnOn                  = 1
    TurnOff                 = 2
    DimUp                   = 3
    DimDown                 = 4
    StartDimUp              = 5
    StartDimDown            = 6
    StopDimming             = 7
    EnableDynamicDimming    = 8
    DisableDynamicDimming   = 9
    EnableDynamicColor      = 10
    DisableDynamicColor     = 11
    SetBrightness           = 12
    SetWhiteTemp            = 13
    SetColor                = 14
    Rename                  = 15
    Refresh                 = 16

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
