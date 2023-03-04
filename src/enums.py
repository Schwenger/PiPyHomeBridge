"Collecting enums."

from enum import Enum
from typing import Optional

# pylint: disable="invalid-name"
class DeviceKind(Enum):
    "Kind of device"
    Light = "Light"
    Remote = "Remote"
    Outlet = "Outlet"

    @staticmethod
    def from_str(val: str) -> Optional['DeviceKind']:
        "Creates a device kind from a string if possible."
        if val not in DeviceKind._member_names_: # pylint: disable=no-member
            return None
        return DeviceKind[val]

# pylint: disable="invalid-name"
class Vendor(Enum):
    "List of known vendors"
    Ikea = "Ikea"
    Hue = "Hue"
    Other = "Other"

class TopicCommand(Enum):
    "Different Commands"
    GET = "get"
    SET = "set"

    @staticmethod
    def from_str(val: str) -> Optional['TopicCommand']:
        "Creates a topic command from a string if possible."
        if val not in TopicCommand._member_names_: # pylint: disable=no-member
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

    @staticmethod
    def from_str(val: str) -> Optional['ApiCommand']:
        "Creates a command from a string if possible."
        if val not in ApiCommand._member_names_: # pylint: disable=no-member
            return None
        return ApiCommand[val]

# pylint: disable=invalid-name
class ApiQuery(Enum):
    "A query retrieved over the Api"
    Rooms = 1

    @staticmethod
    def from_str(val: str) -> Optional['ApiQuery']:
        "Creates a command from a string if possible."
        if val not in ApiQuery._member_names_: # pylint: disable=no-member
            return None
        return ApiQuery[val]

# pylint: disable=invalid-name
class QDataKind(Enum):
    "Kind of a queue data"
    Status = 2
    ApiAction = 3
    Refresh = 4
    ApiQuery = 5

# pylint: disable=invalid-name
class TopicTarget(Enum):
    "Entities addressable via a topic."
    Device = "Device"
    Remote = "Remote"
    Home   = "Home"
    Room   = "Room"
    Group  = "Group"

    @staticmethod
    def from_str(val: str) -> Optional['TopicTarget']:
        "Creates a topic target from a string if possible."
        if val not in TopicTarget._member_names_: # pylint: disable=no-member
            return None
        return TopicTarget[val]
