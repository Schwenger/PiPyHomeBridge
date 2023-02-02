"All things related to remotes"
from enum import Enum
from typing import Callable, List
from device import Device

class Button(Enum):
    "Abstract button class"

class DimmerButtons(Button):
    "Enumeration of all dimmer action kinds"
    ON = "on"
    OFF = "off"

class IkeaMultiRemoteButtons(Button):
    "Enumeration of all ikea multi remote action kinds"
    TOGGLE                  = "toggle"
    ARROW_LEFT_CLICK        = "arrow_left_click"
    ARROW_LEFT_HOLD         = "arrow_left_hold"
    ARROW_LEFT_RELEASE      = "arrow_left_release"
    ARROW_RIGHT_CLICK       = "arrow_right_click"
    ARROW_RIGHT_HOLD        = "arrow_right_hold"
    ARROW_RIGHT_RELEASE     = "arrow_right_release"
    BRIGHTNESS_DOWN_CLICK   = "brightness_down_click"
    BRIGHTNESS_DOWN_HOLD    = "brightness_down_hold"
    BRIGHTNESS_DOWN_RELEASE = "brightness_down_release"
    BRIGHTNESS_UP_CLICK     = "brightness_up_click"
    BRIGHTNESS_UP_HOLD      = "brightness_up_hold"
    BRIGHTNESS_UP_RELEASE   = "brightness_up_release"

class RemoteAction:
    "Contains the constituents to a button action"
    def __init__(self, button: Button, action: Callable):
        self.button = button
        self.action = action

class Remote(Device):
    "Represents a remote."
    def __init__(self, name: str, room: str, actions: List[RemoteAction]):
        super().__init__(name=name, room=room, kind="Remote")
        self.actions = dict(map(lambda a: (a.button.value, a.action), actions))

    def execute_command(self, client, action):
        "Executes a command received from the remote."
        if action in self.actions:
            action = self.actions[action]
            action(client)

    @staticmethod
    def default_dimmer(room, name: str = "Dimmer"):
        "Creates a default dimmer remote for a room."
        actions = [
            RemoteAction( DimmerButtons.ON, room.lights_on ),
            RemoteAction( DimmerButtons.OFF, room.lights_off ),
        ]
        return Remote(name, room.name, actions)

    @staticmethod
    def default_ikea_remote(room, name: str = "Remote"):
        "Creates a default ikea remote for a room."
        actions = [
            RemoteAction(
                IkeaMultiRemoteButtons.TOGGLE,
                room.toggle_lights
            ),
            RemoteAction(
                IkeaMultiRemoteButtons.ARROW_LEFT_CLICK,
                room.shift_color_counter_clockwise
            ),
            RemoteAction(
                IkeaMultiRemoteButtons.ARROW_RIGHT_CLICK,
                room.shift_color_clockwise
            ),
            RemoteAction(
                IkeaMultiRemoteButtons.BRIGHTNESS_DOWN_CLICK,
                room.dim
            ),
            RemoteAction(
                IkeaMultiRemoteButtons.BRIGHTNESS_UP_CLICK,
                room.brighten
            ),
            RemoteAction(
                IkeaMultiRemoteButtons.BRIGHTNESS_UP_HOLD,
                room.disable_adaptive_dimming
            ),
            RemoteAction(
                IkeaMultiRemoteButtons.BRIGHTNESS_DOWN_HOLD,
                room.enable_adaptive_dimming
            ),
            RemoteAction(
                IkeaMultiRemoteButtons.ARROW_LEFT_HOLD,
                room.enable_colorful
            ),
            RemoteAction(
                IkeaMultiRemoteButtons.ARROW_RIGHT_HOLD,
                room.disable_colorful
            ),
        ]
        return Remote(name, room.name, actions)
