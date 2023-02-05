"All things related to remotes"
from enum import Enum
from typing import Callable, List
from paho.mqtt import client as mqtt
from device import Device
import log

class Button(Enum):
    "Abstract button class"

class DimmerButtons(Button):
    "Enumeration of all dimmer action kinds"
    ON = "on"
    OFF = "off"
    BRIGHTNESS_MOVE_UP   = "brightness_move_up"
    BRIGHTNESS_MOVE_DOWN = "brightness_move_down"
    BRIGHTNESS_STOP      = "brightness_stop"

class IkeaMultiButton(Button):
    "Enumeration of all ikea multi remote action kinds"
    TOGGLE                  = "toggle"
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

    def consume_message(self, client: mqtt.Client, data):
        if "action" not in data:
            log.alert("Message to remote without action found!")
            log.alert("Addressed to " + str(self.topic()))
            log.alert("Payload: " + str(data))
        self.execute_command(client, data["action"])

    @staticmethod
    def default_dimmer(room, name: str = "Dimmer"):
        "Creates a default dimmer remote for a room."
        actions = [
            RemoteAction( DimmerButtons.ON,  room.lights_on ),
            RemoteAction( DimmerButtons.OFF, room.lights_off ),
            RemoteAction( DimmerButtons.BRIGHTNESS_MOVE_DOWN, room.start_dim_down ),
            RemoteAction( DimmerButtons.BRIGHTNESS_MOVE_UP,   room.start_dim_up ),
            RemoteAction( DimmerButtons.BRIGHTNESS_STOP,      room.stop_dim ),
        ]
        return Remote(name, room.name, actions)

    @staticmethod
    def default_ikea_remote(room, name: str = "Remote"):
        "Creates a default ikea remote for a room."
        actions = [
            RemoteAction( IkeaMultiButton.TOGGLE, room.toggle_lights ),
            RemoteAction( IkeaMultiButton.ARR_LEFT_CLICK, room.shift_color_counter_clockwise ),
            RemoteAction( IkeaMultiButton.ARR_RIGHT_CLICK, room.shift_color_clockwise ),
            RemoteAction( IkeaMultiButton.ARR_LEFT_HOLD, room.enable_colorful ),
            RemoteAction( IkeaMultiButton.ARR_RIGHT_HOLD, room.disable_colorful ),
            RemoteAction( IkeaMultiButton.BRI_DOWN_CLICK, room.dim ),
            RemoteAction( IkeaMultiButton.BRI_UP_CLICK, room.brighten),
            RemoteAction( IkeaMultiButton.BRI_UP_HOLD, room.start_dim_up ),
            RemoteAction( IkeaMultiButton.BRI_DOWN_HOLD, room.start_dim_down ),
            RemoteAction( IkeaMultiButton.BRI_UP_RELEASE, room.stop_dim ),
            RemoteAction( IkeaMultiButton.BRI_DOWN_RELEASE, room.stop_dim ),
        ]
        return Remote(name, room.name, actions)
