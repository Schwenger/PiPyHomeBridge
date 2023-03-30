"All enums that cannot be modified without reflecting the change in swift."

from enum import Enum, auto
from typing import Optional, Type, TypeVar

from strenum import PascalCaseStrEnum

FfiEnumT = TypeVar('FfiEnumT', bound=Enum)

class FfiEnum(PascalCaseStrEnum):
    "An enum that can be sent to and fro Swift."

    @classmethod
    def from_str(cls: Type[FfiEnumT], value: str) -> Optional[FfiEnumT]:
        "Creates the enum from a string if possible."
        return cls.__members__.get(value)


# pylint: disable="invalid-name"
class DeviceKind(FfiEnum):
    "Kind of device"
    Light  = auto()
    Remote = auto()
    Outlet = auto()


# pylint: disable="invalid-name"
class Vendor(FfiEnum):
    "List of known vendors"
    Ikea  = auto()
    Hue   = auto()
    Other = auto()

# pylint: disable="invalid-name"
class DeviceModel(FfiEnum):
    "A list of device models supported."
    IkeaDimmer      = auto()
    IkeaMultiButton = auto()
    IkeaDimmable    = auto()
    IkeaOutlet      = auto()
    HueColor        = auto()

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

    @property
    def is_dimmable(self) -> bool:
        "Indicates if the device is capable of being dimmed."
        return {
            DeviceModel.IkeaDimmer:      False,
            DeviceModel.IkeaOutlet:      False,
            DeviceModel.IkeaMultiButton: False,
            DeviceModel.IkeaDimmable:    True,
            DeviceModel.HueColor:        True,
        }[self]

    @property
    def is_color(self) -> bool:
        "Indicates if the device is capable of emitting colored light."
        return {
            DeviceModel.IkeaDimmer:      False,
            DeviceModel.IkeaOutlet:      False,
            DeviceModel.IkeaMultiButton: False,
            DeviceModel.IkeaDimmable:    False,
            DeviceModel.HueColor:        True,
        }[self]
