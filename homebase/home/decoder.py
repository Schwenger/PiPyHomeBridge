"Decodes a home specification."

from typing import Dict, List, Optional

import lighting
import lighting.config
import yaml
from comm import Topic
from enums import DeviceModel
from home.home import Home
from home.room import Room
from remote import Remote
from sensor import Sensor


def read(path: str) -> Home:
    "Decodes a specification behind the given path into a Home or raises an error."
    home = __read(path)
    rooms = list(map(__decode_room, home["rooms"]))
    return Home(rooms)

def __decode_room(room: dict) -> Room:
    name = room["name"]
    icon = room["icon"]
    main_group = __decode_light_group(room["lights"], name, [])
    targets = __collect_viable_targets(main_group)
    targets[name] = Topic.for_room(name)
    remotes = __decode_remotes(room=room, room_name=name, targets=targets)
    sensors = __decode_sensors(room=room, room_name=name)
    return Room(name, group=main_group, icon=icon, remotes=remotes, sensors=sensors)

def __decode_light_group(group: dict, room: str, hierarchie: List[str]) -> lighting.Group:
    name = group["name"]
    singles = list(map(lambda l: __decode_light(l, room), group["singles"]))
    subs = []
    for sub in (group.get("subgroups") or []):
        sub = __decode_light_group(sub, room, hierarchie + [name])
        subs.append(sub)
    return lighting.Group(
        single_lights=singles,
        name=name,
        room=room,
        groups=subs,
        hierarchie=hierarchie,
        config=__decode_config(group["config"])
    )

def __decode_config(config: Optional[dict]) -> lighting.Config:
    from lighting.config import Override  # pylint: disable=import-outside-toplevel
    colorful = Override.none()
    dynamic = Override.none()
    hue = Override.none()
    saturation = Override.none()
    lumin = Override.none()
    if config is not None:
        if "colorful" in config:
            colorful   = Override.perm(bool(config["colorful"]))
        if "dynamic" in config:
            dynamic    = Override.perm(bool(config["dynamic"]))
        if "hue" in config:
            hue        = Override.perm(float(config["hue"]))
        if "saturation" in config:
            saturation = Override.perm(float(config["saturation"]))
        if "lumin" in config:
            lumin      = Override.perm(float(config["lumin"]))
    return lighting.Config(
        toggled_on=Override.perm(False),
        colorful=colorful,
        dynamic=dynamic,
        hue=hue,
        saturation=saturation,
        lumin_mod=lumin,
    )

def __decode_light(light: dict, room: str) -> lighting.Concrete:
    name = light["name"]
    kind = light["kind"]
    icon = light["icon"]
    config = __decode_config(light["config"])
    model = DeviceModel.from_str(light["model"])
    assert model is not None
    ident = light["id"]
    if kind == "Simple":
        return lighting.simple(
            name=name, room=room, icon=icon, ident=ident, model=model, config=config
        )
    if kind in ["Dimmable", "Color"]:
        return lighting.regular(
            name=name, room=room, icon=icon, ident=ident, model=model, config=config
        )
    assert False

def __decode_remotes(room: dict, room_name: str, targets: Dict[str, Topic]) -> List[Remote]:
    remotes = []
    for remote in (room.get("remotes") or []):
        rem = __decode_remote(remote, room=room_name, targets=targets)
        remotes.append(rem)
    return remotes

def __decode_remote(remote: dict, room: str, targets: Dict[str, Topic]) -> Remote:
    name = remote["name"]
    kind = remote["kind"]
    icon = remote["icon"]
    ident = remote["id"]
    target_name = remote["controls"]
    target = targets[target_name]
    if kind == "DefaultDimmer":
        return Remote.default_dimmer(
            room=room,
            ident=ident,
            icon=icon,
            controls=target,
            name=name
        )
    if kind == "IkeaMulti":
        return Remote.default_ikea_remote(
            room=room,
            ident=ident,
            icon=icon,
            controls=target,
            name=name
        )
    assert False

def __decode_sensors(room: dict, room_name: str) -> List[Sensor]:
    sensors = []
    for sensor in (room.get("sensors") or []):
        sens = __decode_sensor(sensor, room=room_name)
        sensors.append(sens)
    return sensors

def __decode_sensor(sensor: dict, room: str) -> Sensor:
    name  = sensor["name"]
    model = sensor["model"]
    icon = sensor["icon"]
    ident = sensor["id"]
    model = DeviceModel.from_str(model)
    assert model is not None
    return Sensor(name=name, room=room, icon=icon, model=model, ident=ident)

def __collect_viable_targets(grp: lighting.Group) -> Dict[str, Topic]:
    res = { grp.name: grp.topic }
    for sub in grp.groups:
        other = __collect_viable_targets(sub)
        res = { **res, **other }
    return res

def __read(path) -> dict:
    with open(path, "r", encoding="utf-8") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as yml_exc:
            print("Failed to load config file config.yml.")
            raise yml_exc
