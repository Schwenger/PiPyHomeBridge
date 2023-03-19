"Anything related to zigbee topics."

import logging
from typing import List, Optional, Tuple

from enums import DeviceKind, TopicCommand, TopicTarget
from homebaseerror import HomeBaseError


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
        target: TopicTarget,
        name:   str,
        sub_names: List[str],
        device_id: Optional[Tuple[DeviceKind, str]] = None,
    ):
        if (device_id is not None) != (target is TopicTarget.Device):
            raise HomeBaseError.Unreachable
        self.target = target
        self.name = name
        self.device_id = device_id
        self.sub_names = sub_names
        self._comps = [Topic.BASE, target.value] + sub_names + [name]
        if device_id is not None:
            self._comps.insert(2, device_id[0].value)
            self._comps.append(device_id[1])

    @property
    def string(self) -> str:
        "Returns a string representation of the topic."
        return self._join(self._comps)

    @property
    def without_base(self) -> str:
        "Returns the topic omitting the base."
        return self._join(self._comps[1:])

    def as_set(self) -> str:
        "Returns this topic as a set-command."
        return self._join(self._comps + [TopicCommand.SET.value])

    def as_get(self) -> str:
        "Returns this topic as a get-command."
        return self._join(self._comps + [TopicCommand.GET.value])

    @staticmethod
    def from_str(string: str) -> 'Topic':
        "Creates a topic from a string.  Asserts proper format. May not be a command."
        split = string.split(Topic.SEP)
        if len(split) < 3 or split[0] != Topic.BASE:
            logging.error("Topic %s misses base or has less than 3 components.", string)
            raise HomeBaseError.TopicParseError
        target = TopicTarget.from_str(split[1])
        if target is None:
            logging.error("Topic %s has an invalid target.", string)
            raise HomeBaseError.TopicParseError
        name = split[-1]
        groups = split[2:-1]
        device_id: Optional[Tuple[DeviceKind, str]] = None
        if target is TopicTarget.Device:
            if len(groups) < 2:
                logging.error("Topic %s has less than two groups but is a device.", string)
                raise HomeBaseError.TopicParseError
            ident = name
            name = groups[-1]
            device_kind = DeviceKind.from_str(groups[0])
            if device_kind is None:
                logging.error("Topic %s has an invalid device kind.", string)
                raise HomeBaseError.TopicParseError
            groups = groups[1:-1]
            device_id = (device_kind, ident)
        return Topic(
            target=target,
            name=name,
            sub_names=groups,
            device_id=device_id
        )

    @staticmethod
    def for_home() -> 'Topic':
        'Creates a topic for refering to the home.'
        return Topic(
            target=TopicTarget.Home,
            name="Home",
            sub_names=[]
        )

    @staticmethod
    def for_bridge(categories: List[str], name: str) -> 'Topic':
        'Creates a topic for bridge events.'
        return Topic(
            target=TopicTarget.Bridge,
            name=name,
            sub_names=categories
        )

    @staticmethod
    def for_room(name: str) -> 'Topic':
        'Creates a topic for refering to a room.'
        return Topic(
            target=TopicTarget.Room,
            name=name,
            sub_names=[]
        )

    @staticmethod
    def for_group(hierarchie: List[str]) -> 'Topic':
        'Creates a topic for refering to a group.'
        if len(hierarchie) == 0:
            raise HomeBaseError.Unreachable
        return Topic(
            target=TopicTarget.Group,
            name=hierarchie[-1],
            sub_names=hierarchie[:-1]
        )

    @staticmethod
    def for_device(
        name: str,
        kind: DeviceKind,
        ident: str,
        groups: List[str]
    ) -> 'Topic':
        'Creates a topic for refering to a device.'
        return Topic(
            target=TopicTarget.Device,
            device_id=(kind, ident),
            name=name,
            sub_names=groups,
        )

    @staticmethod
    def _join(parts: List[str]) -> str:
        return "/".join(parts)

    def __str__(self):
        return self.string

    def __eq__(self, other):
        if not isinstance(other, Topic):
            return NotImplemented
        return self.string == other.string
