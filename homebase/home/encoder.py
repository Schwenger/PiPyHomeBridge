"Encodes a home into a yml description."

from typing import Dict

import lighting
import yaml
from enums import DeviceModel
from home.home import Home
from home.room import Room
from remote import Remote


def write(home: Home, path: str):
    "Encodes the home in yml format."
    res = {}
    rooms = list(map(__encode_room, home.rooms))
    res["rooms"] = rooms
    __write(path, res)

def __encode_room(room: Room) -> dict:
    remotes = list(map(__encode_remote, room.remotes))
    return {
        "name": room.name,
        "lights": __encode_light_group(room.group),
        "remotes": remotes
    }

def __encode_light_group(group: lighting.Group) -> dict:
    return {
        "name": group.name,
        "singles": list(map(__encode_light, group.single_lights)),
        "subgroups": list(map(__encode_light_group, group.groups))
    }

def __encode_light(light: lighting.Concrete) -> Dict[str, str]:
    if light.is_color:
        kind = "Color"
    elif light.is_dimmable:
        kind = "Dimmable"
    else:
        kind = "Simple"
    return {
        "name": light.name,
        "kind": kind,
        "model": light.model.value,
        "id": light.ident,
    }

def __encode_remote(remote: Remote) -> Dict[str, str]:
    if remote.model == DeviceModel.IkeaMultiButton:
        kind = "IkeaMulti"
    elif remote.model == DeviceModel.IkeaDimmer:
        kind = "DefaultDimmer"
    else:
        assert False
    return {
        "name": remote.name,
        "kind": kind,
        "id": remote.ident,
        "controls": remote.controls_topic.name
    }


def __write(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as stream:
        try:
            yaml.safe_dump(data, stream=stream)
        except yaml.YAMLError as yml_exc:
            print("Failed to load config file config.yml.")
            raise yml_exc
