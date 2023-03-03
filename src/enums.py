"Collecting enums."

from enum import Enum

# pylint: disable="invalid-name"
class DeviceKind(Enum):
    "Kind of device"
    Light = "Light"
    Remote = "Remote"
    Outlet = "Outlet"

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
