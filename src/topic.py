"Anything related to zigbee topics."

from typing import Optional, List

class Topic:
    """
    Represents topics in the zigbee protocol.
    Starts with a base, followed by a room and the name of the object.
    Might be extended in the future.
    """
    BASE = "zigbee2mqtt"
    SEP = "/"
    def __init__(
        self,
        device: str,
        room: str,
        name: str,
        floor: str = "Main",
        groups: Optional[List[str]] = None
    ):
        self.name = name
        self.device = device
        self.room = room
        self.floor = floor
        self.groups = groups or []
        self._comps: List[str] = [Topic.BASE, device, floor, room] + self.groups + [name]

    @property
    def string(self) -> str:
        "Returns a string representation of the topic."
        return self._join(self._comps)

    @property
    def without_base(self) -> str:
        "Returns the topic omitting the base."
        return self._join(self._comps[1:])

    @staticmethod
    def _join(parts: List[str]) -> str:
        return "/".join(parts)

    def as_set(self) -> str:
        "Returns this topic as a set-command."
        return self.string + Topic.SEP + "set"

    def as_get(self) -> str:
        "Returns this topic as a get-command."
        return self.string + Topic.SEP + "get"

    @staticmethod
    def from_str(string: str) -> 'Topic':
        "Creates a topic from a string.  Asserts proper format. May not be a command."
        split = string.split(Topic.SEP)
        assert len(split) >= 5
        assert split[0] == Topic.BASE
        assert split[-1] not in ["set", "get"]
        device = split[1]
        floor = split[2]
        room = split[3]
        groups = split[4:-1]
        name = split[-1]
        return Topic(name=name, device=device, room=room, floor=floor, groups=groups)

    def __str__(self):
        return self.string
