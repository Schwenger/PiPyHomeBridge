"All things related to remotes"
from enum import Enum
from typing import Dict, Optional, Callable
from queue_data import ApiCommand
from device import Device, DeviceKind, Vendor

class RemoteButton(Enum):
    "Abstract button class"
    @classmethod
    def has_value(cls, value) -> bool:
        "Indicates if the value is a member of the enum"
        return value in cls._value2member_map_

class DimmerButtons(RemoteButton):
    "Enumeration of all dimmer action kinds"
    ON  = "on"
    OFF = "off"
    BRIGHTNESS_MOVE_UP   = "brightness_move_up"
    BRIGHTNESS_MOVE_DOWN = "brightness_move_down"
    BRIGHTNESS_STOP      = "brightness_stop"

    @staticmethod
    def from_str(str_value: str) -> RemoteButton:
        "Creates a remote button based on the string.  Crashes if impossible"
        return DimmerButtons(str_value)


class IkeaMultiButton(RemoteButton):
    "Enumeration of all ikea multi remote action kinds"
    TOGGLE           = "toggle"
    ARR_LEFT_CLICK   = "arrow_left_click"
    ARR_LEFT_HOLD    = "arrow_left_hold"
    ARR_LEFT_RELEASE = "arrow_left_release"
    ARR_RIGHT_CLICK  = "arrow_right_click"
    ARR_RIGHT_HOLD   = "arrow_right_hold"
    ARR_RIGHT_RELEASE= "arrow_right_release"
    BRI_DOWN_CLICK   = "brightness_down_click"
    BRI_DOWN_HOLD    = "brightness_down_hold"
    BRI_DOWN_RELEASE = "brightness_down_release"
    BRI_UP_CLICK     = "brightness_up_click"
    BRI_UP_HOLD      = "brightness_up_hold"
    BRI_UP_RELEASE   = "brightness_up_release"

    @staticmethod
    def from_str(str_value: str) -> RemoteButton:
        "Creates a remote button based on the string.  Crashes if impossible"
        return IkeaMultiButton(str_value)

class Remote(Device):
    "Represents a remote."
    def __init__(self,
        name: str,
        room: str,
        button_from_str: Callable[[str], RemoteButton],
        actions: Dict[RemoteButton, ApiCommand]
    ):
        super().__init__(name=name, room=room, kind=DeviceKind.Remote, vendor=Vendor.Ikea)
        self._button_from_str = button_from_str
        self._actions: Dict[RemoteButton, ApiCommand] = actions

    def cmd_for_action(self, action: str) -> Optional[ApiCommand]:
        "Returns the api command corresponding to the button press if defined."
        button = self._button_from_str(action)
        assert button is not None
        return self._actions[button]

    @staticmethod
    def default_dimmer(room: str, name: str = "Dimmer"):
        "Creates a default dimmer remote for a room."
        actions: Dict[RemoteButton, ApiCommand] = {
            DimmerButtons.ON:   ApiCommand.TurnOn,
            DimmerButtons.OFF:  ApiCommand.TurnOff,
            DimmerButtons.BRIGHTNESS_MOVE_DOWN: ApiCommand.StartDimdown,
            DimmerButtons.BRIGHTNESS_MOVE_UP:   ApiCommand.StartDimUp,
            DimmerButtons.BRIGHTNESS_STOP:      ApiCommand.StopDimming,
        }
        return Remote(name, room, DimmerButtons.from_str, actions)

    @staticmethod
    def default_ikea_remote(room: str, name: str = "Remote"):
        "Creates a default ikea remote for a room."
        actions: Dict[RemoteButton, ApiCommand] = {
            IkeaMultiButton.TOGGLE: ApiCommand.Toggle,
            IkeaMultiButton.ARR_LEFT_CLICK: ApiCommand.DisableDynamicDimming,
            IkeaMultiButton.ARR_RIGHT_CLICK: ApiCommand.EnableDynamicDimming,
            IkeaMultiButton.ARR_LEFT_HOLD: ApiCommand.DisableDynamicColor,
            IkeaMultiButton.ARR_RIGHT_HOLD: ApiCommand.EnableDynamicColor,
            IkeaMultiButton.BRI_UP_CLICK: ApiCommand.DimUp,
            IkeaMultiButton.BRI_UP_HOLD: ApiCommand.StartDimUp,
            IkeaMultiButton.BRI_UP_RELEASE: ApiCommand.StopDimming,
            IkeaMultiButton.BRI_DOWN_CLICK: ApiCommand.DimDown,
            IkeaMultiButton.BRI_DOWN_HOLD: ApiCommand.StartDimdown,
            IkeaMultiButton.BRI_DOWN_RELEASE: ApiCommand.StopDimming,
        }
        return Remote(name, room, IkeaMultiButton.from_str, actions)
