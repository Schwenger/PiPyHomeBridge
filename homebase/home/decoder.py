"Decodes a home specification."

from typing import Dict, List

import lighting
import yaml
from comm.topic import Topic
from enums import DeviceModel
from home.home import Home
from home.remote import Remote
from home.room import Room


def read(path: str) -> Home:
    "Parses a specification behind the given path into a Home or raises an error."
    home = __read(path)
    rooms = []
    for room in home["rooms"]:
        name = room["name"]
        main_group = __parse_light_group(room["lights"], name, [])
        targets = __collect_viable_targets(main_group)
        targets[name] = Topic.for_room(name)
        remotes = __parse_remotes(room=room, room_name=name, targets=targets)
        room = Room(name, main_group, remotes=remotes)
        rooms.append(room)
    return Home()#rooms)

def __parse_light_group(group: dict, room: str, hierarchie: List[str]) -> lighting.Group:
    name = group["name"]
    singles = list(map(lambda l: __parse_light(l, room), group["singles"]))
    hierarchie.append(name)
    subs = []
    for sub in (group.get("subgroups") or []):
        sub = __parse_light_group(sub, room, hierarchie)
        subs.append(sub)
    return lighting.Group(
        single_lights=singles,
        name=name,
        groups=subs,
        hierarchie=hierarchie
    )

def __parse_light(light: dict, room: str) -> lighting.Concrete:
    name = light["name"]
    kind = light["kind"]
    model = DeviceModel.from_str(light["model"])
    assert model is not None
    ident = light["id"]
    if kind == "Simple":
        return lighting.simple(
            name=name, room=room, ident=ident, model=model
        )
    if kind == "Dimmable":
        return lighting.dimmable(
            name=name, room=room, ident=ident, model=model
        )
    if kind == "Color":
        return lighting.color(
            name=name, room=room, ident=ident, model=model
        )
    assert False

def __parse_remotes(room: dict, room_name: str, targets: Dict[str, Topic]) -> List[Remote]:
    remotes = []
    if "remotes" in room:
        for remote in room["remotes"]:
            rem = __parse_remote(remote, room=room_name, targets=targets)
            remotes.append(rem)
    return remotes

def __parse_remote(remote: dict, room: str, targets: Dict[str, Topic]) -> Remote:
    name = remote["name"]
    kind = remote["kind"]
    ident = remote["id"]
    target_name = remote["controls"]
    target = targets[target_name]
    if kind == "DefaultDimmer":
        return Remote.default_dimmer(
            room=room,
            ident=ident,
            controls=target,
            name=name
        )
    if kind == "IkeaMulti":
        return Remote.default_ikea_remote(
            room=room,
            ident=ident,
            controls=target,
            name=name
        )
    assert False

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

# def living_room() -> Room:
#     "Creates an instance of the living room."
#     name = "Living Room"
#     lights_list: List[ConcreteLight] = [
#         lighting.simple(
#             name="Comfort Light",
#             room=name,
#             model=DeviceModel.IkeaOutlet,
#             ident="aaaa",
#         ),
#         lighting.dimmable(
#             name="Uplight/Reading",
#             room=name,
#             model=DeviceModel.IkeaDimmable,
#             ident="aaab",
#         ),
#         lighting.white(
#             name="Uplight/Main",
#             room=name,
#             model=DeviceModel.HueColor,
#             ident="aaac",
#         ),
#         lighting.color(
#             name="Orb",
#             room=name,
#             model=DeviceModel.HueColor,
#             ident="aaad"
#         ),
#     ]

#     lights = lighting.Group(
#         name="Main",
#         single_lights=lights_list,
#         hierarchie=[name],
#         groups=[]
#     )
#     room_topic = Topic.for_room(name)
#     remotes = [
#         Remote.default_ikea_remote(name, controls=room_topic, ident="bbbc"),
#         Remote.default_dimmer(name, controls=room_topic, name="Dimmer", ident="bbbb")
#     ]
#     return Room(name, lights, remotes)
