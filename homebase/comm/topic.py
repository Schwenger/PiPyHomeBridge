"Anything related to zigbee topics."

from typing import List, Optional

from enums import DeviceKind, TopicCommand, TopicCategory
from homebaseerror import HomeBaseError
from common import Log


class Topic:
    """
    Represents topics in the zigbee protocol.
    """
    BASE = "zigbee2mqtt"
    SEP = "/"

    KEEP_IT_INTERNAL = object()

    def __init__(
        self,
        category: TopicCategory,
        device_kind: Optional[DeviceKind],
        room: Optional[str],
        groups: Optional[List[str]],
        name: Optional[str],
        key
    ):
        """
            Base/Category/'home'
                for Cat ∈ {Home}
            Base/Category/'event'
                for Cat ∈ {bridge}
            Base/Category/Room
                for Cat ∈ {Room}
            Base/Category/Room/Group1/.../Groupn/Name
                for Cat ∈ {Group}
            Base/Category/Device/Room/Group1/.../Groupn/Name
                for Cat ∈ {Device}, Device ∈ {Sensor, Light, Outlet, Remote}
        """
        assert key == Topic.KEEP_IT_INTERNAL
        if category == TopicCategory.Home:
            assert device_kind is None and room is None and groups is None and name is None
            self._comps = [Topic.BASE, category, 'home']
        if category == TopicCategory.Bridge:
            assert device_kind is None and room is None and groups is None and name is None
            self._comps = [Topic.BASE, category, 'bridge']
        if category == TopicCategory.Room:
            assert device_kind is None and name is None and groups is None
            assert room is not None
            self._comps = [Topic.BASE, category, room]
        if category == TopicCategory.Group:
            assert device_kind is None
            assert room is not None and groups is not None and name is not None
            self._comps = [Topic.BASE, category, room] + groups + [name]
        if category == TopicCategory.Device:
            assert room is not None and groups is not None
            assert name is not None and device_kind is not None
            self._comps = [Topic.BASE, category, device_kind, room] + groups + [name]
        self.category = category
        self.device_kind = device_kind
        self.room = room
        self.groups = groups
        self.name = name

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
    def for_home() -> 'Topic':
        'Creates a topic for refering to the home.'
        return Topic(
            category=TopicCategory.Home,
            device_kind=None,
            room=None,
            groups=None,
            name=None,
            key=Topic.KEEP_IT_INTERNAL,
        )

    @staticmethod
    def for_bridge() -> 'Topic':
        'Creates a topic for bridge events.'
        return Topic(
            category=TopicCategory.Bridge,
            device_kind=None,
            room=None,
            groups=None,
            name=None,
            key=Topic.KEEP_IT_INTERNAL,
        )

    @staticmethod
    def for_room(name: str) -> 'Topic':
        'Creates a topic for refering to a room.'
        return Topic(
            category=TopicCategory.Room,
            device_kind=None,
            room=name,
            groups=None,
            name=None,
            key=Topic.KEEP_IT_INTERNAL,
        )

    @staticmethod
    def for_group(room: str, hierarchie: List[str], name: str) -> 'Topic':
        'Creates a topic for refering to a group.'
        if len(hierarchie) == 0:
            raise HomeBaseError.Unreachable
        return Topic(
            category=TopicCategory.Group,
            device_kind=None,
            room=room,
            groups=hierarchie,
            name=name,
            key=Topic.KEEP_IT_INTERNAL,
        )

    @staticmethod
    def for_device(
        name: str,
        kind: DeviceKind,
        room: str,
        groups: List[str]
    ) -> 'Topic':
        'Creates a topic for refering to a device.'
        return Topic(
            category=TopicCategory.Device,
            device_kind=kind,
            room=room,
            groups=groups,
            name=name,
            key=Topic.KEEP_IT_INTERNAL
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


    @staticmethod
    def from_str(string: str) -> 'Topic':
        "Creates a topic from a string.  Asserts proper format. May not be a command."
        split = string.split(Topic.SEP)
        if len(split) < 3 or split[0] != Topic.BASE:
            Log.tpc.error("Topic %s misses base or has less than 3 components.", string)
            raise HomeBaseError.TopicParseError
        cat = TopicCategory.from_str(split[1])
        if cat is None:
            Log.tpc.error("Topic %s has an invalid target.", string)
            raise HomeBaseError.TopicParseError
        if cat is TopicCategory.Home:
            if split[2] != 'home' or len(split) != 3:
                Log.tpc.error("Topic with Category Home targets invalid name %s", split[2:])
                raise HomeBaseError.TopicParseError
            return Topic.for_home()
        if cat is TopicCategory.Bridge:
            if split[2] != 'bridge' or len(split) != 3:
                Log.tpc.error("Topic with Category Bridge targets invalid name %s", split[2:])
                raise HomeBaseError.TopicParseError
            return Topic.for_bridge()
        if cat is TopicCategory.Room:
            if len(split) != 3:
                Log.tpc.error("Topic with Category Room has superfluous components %s", split[3:])
                raise HomeBaseError.TopicParseError
            name = split[2]
            return Topic.for_room(split[2])
        if cat is TopicCategory.Group:
            if len(split) < 4:
                Log.tpc.error("Topic with Category Group has to few components %s", split)
                raise HomeBaseError.TopicParseError
            room = split[2]
            groups = split[3:-1]
            name = split[-1]
            return Topic.for_group(room, groups, name)
        if cat is TopicCategory.Device:
            if len(split) < 5:
                Log.tpc.error("Topic with Category Device has to few components %s", split)
                raise HomeBaseError.TopicParseError
            kind = DeviceKind.from_str(split[2])
            if kind is None:
                Log.tpc.error("Invalid device kind %s", split[2])
                raise HomeBaseError.TopicParseError
            room = split[3]
            groups = split[4:-1]
            name = split[-1]
            return Topic.for_device(name, kind, room, groups)
        Log.tpc.error("Invalid Topic %s", split)
        raise HomeBaseError.TopicParseError
