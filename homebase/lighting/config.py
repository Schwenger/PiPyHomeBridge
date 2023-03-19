"Configures an abstract light."

from datetime import datetime as Timestamp
from typing import Generic, Optional, Tuple, TypeVar

from colour import Color
from common import scale_relative


T = TypeVar('T')      # Declare type variable
class _Override(Generic[T]):
    def __init__(
        self,
        permanent: Optional[T],
        temporary: Optional[Tuple[T, Timestamp]],
    ):
        self.permanent = permanent
        self.temporary = temporary

    @property
    def value(self) -> Optional[T]:
        "Provides the permanent or overriden value if any"
        # Todo: Evict temporary configs after a while.
        if self.temporary is not None:
            return self.temporary[0]
        return self.permanent

    @staticmethod
    def none() -> '_Override[T]':
        "Creates a no-op override."
        return _Override(permanent=None, temporary=None)

    @staticmethod
    def perm(pval: T) -> '_Override[T]':
        "Creates a permanent override."
        return _Override(permanent=pval, temporary=None)

    @staticmethod
    def temp(tval: T) -> '_Override[T]':
        "Creates a temporary override."
        return _Override(permanent=None, temporary=(tval, Timestamp.now()))

    def set_temp(self, tval: T):
        "Sets the temporary override value."
        self.temporary = (tval, Timestamp.now())

    def set_permanent(self, pval: T):
        "Sets the permanent override value."
        self.permanent = pval


class Full:
    "Creates a full configuration of a light."
    def __init__(
        self,
        brightness:       float   = 0.7,
        white_temp:       float   = 0.7,
        color:            Color   = Color("White"),
        colorful:         bool    = True,
        dynamic:          bool    = True,
    ):
        self.brightness       = brightness
        self.white_temp       = white_temp
        self.color            = color
        self.colorful         = colorful
        self.dynamic          = dynamic

    def modified_by(self, relative: 'Relative') -> 'Full':
        "Returns itself modified by the relative configuration."
        return relative.modify(self)


class Relative:
    "Creates a realtive configuration used to manipulate a configuration."
    def __init__(
        self,
        brightness:       _Override[float]   = _Override.none(),
        white_temp:       _Override[float]   = _Override.none(),
        color_offset:     _Override[int]     = _Override.none(),
        colorful:         _Override[bool]    = _Override.none(),
        dynamic:          _Override[bool]    = _Override.none(),
    ):
        self.brightness       = brightness     # Between -1 and +1
        self.white_temp       = white_temp     # Between -1 and +1
        self.color_offset     = color_offset   # Between 0 and 5
        self.colorful         = colorful
        self.dynamic          = dynamic

    def modify(self, full: Full) -> Full:
        "Modifies a full configuration."
        brightness_mod = self.brightness.value or 0.0
        brightness = scale_relative(value=full.brightness, scale=brightness_mod * 0.2)
        white_temp_mod = self.white_temp.value or 0.0
        white_temp = scale_relative(value=full.white_temp, scale=white_temp_mod * 0.2)
        color_offset   = self.color_offset.value or 0
        color = full.color
        color.hue += 0.2 * color_offset
        return Full(
            brightness=brightness,
            white_temp=white_temp,
            color=color,
            colorful=self.colorful.value or full.colorful,
            dynamic=self.dynamic.value or full.dynamic,
        )
