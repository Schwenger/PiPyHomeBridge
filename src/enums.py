"Collecting enums."

from enum import Enum
from typing import Optional

# pylint: disable="invalid-name"
class Vendor(Enum):
    "List of known vendors"
    Ikea = "Ikea"
    Hue = "Hue"
    Other = "Other"

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
class DeviceModel(Enum):
    "A list of device models supported."
    IkeaDimmer = "IkeaDimmer"
    IkeaMultiButton = "IkeaMultiButton"
    IkeaDimmable = "IkeaDimmable"
    IkeaOutlet = "IkeaOutlet"
    HueColor = "HueColor"

    @property
    def vendor(self) -> Vendor:
        "Specifies the vendor of the device, Ikea or Hue."
        return {
            DeviceModel.IkeaDimmer:      Vendor.Ikea,
            DeviceModel.IkeaOutlet:      Vendor.Ikea,
            DeviceModel.IkeaMultiButton: Vendor.Ikea,
            DeviceModel.IkeaDimmable:    Vendor.Ikea,
            DeviceModel.HueColor:        Vendor.Hue,
        }[self]

    @property
    def kind(self) -> DeviceKind:
        "Specifies the physical kind of the device."
        return {
            DeviceModel.IkeaDimmer:      DeviceKind.Remote,
            DeviceModel.IkeaOutlet:      DeviceKind.Outlet,
            DeviceModel.IkeaMultiButton: DeviceKind.Remote,
            DeviceModel.IkeaDimmable:    DeviceKind.Light,
            DeviceModel.HueColor:        DeviceKind.Light,
        }[self]

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
    Structure  = 1
    LightState = 2

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
    Bridge = "Bridge"

    @staticmethod
    def from_str(val: str) -> Optional['TopicTarget']:
        "Creates a topic target from a string if possible."
        if val not in TopicTarget._member_names_: # pylint: disable=no-member
            return None
        return TopicTarget[val]

class HomeBaseError(Exception, Enum):
    "General error class"
    PayloadNotFound = "Could not find a they required payload."
    RoomNotFound = "Could not find room."
    RemoteNotFound = "Could not find remote."
    Unreachable = "Some programmer error occured."
    LightNotFound = "Could not find light."
    InvalidRemoteAction = "Cannot determine the action of a remote operation."
    TopicParseError = "Failed to parse remote string."
