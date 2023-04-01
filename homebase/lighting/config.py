"Configures an abstract light."

from datetime import datetime as Timestamp
from typing import Callable, Generic, Optional, Tuple, TypeVar

from colour import Color
from lighting.state import State
from common import scale_relative

T = TypeVar('T')
class Override(Generic[T]):
    "Defines an abstract overriding behavior."

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
        self.__evict()
        if self.temporary is not None:
            return self.temporary[0]
        return self.permanent

    def value_or(self, alt: T) -> T:
        "Provides the permanent or overriden value if any"
        self.__evict()
        if self.temporary is not None:
            return self.temporary[0]
        if self.permanent is not None:
            return self.permanent
        return alt

    @staticmethod
    def none() -> 'Override[T]':
        "Creates a no-op override."
        return Override(permanent=None, temporary=None)

    @staticmethod
    def perm(pval: T) -> 'Override[T]':
        "Creates a permanent override."
        return Override(permanent=pval, temporary=None)

    @staticmethod
    def temp(tval: T) -> 'Override[T]':
        "Creates a temporary override."
        return Override(permanent=None, temporary=(tval, Timestamp.now()))

    def set_temp(self, tval: T):
        "Sets the temporary override value."
        self.temporary = (tval, Timestamp.now())

    def modify_temp(self, dft: T, func: Callable[[T], T]):
        "Sets the temporary override value."
        self.__evict()
        if self.temporary is None:
            self.set_temp(func(dft))
            return
        self.set_temp(func(self.temporary[0]))

    def set_permanent(self, pval: T):
        "Sets the permanent override value."
        self.permanent = pval

    def with_parent(self, parent: 'Override[T]') -> 'Override[T]':
        "Returns an override with the own property if present, otherwise the parent's."
        return Override(
            permanent=self.permanent or parent.permanent,
            temporary=self.temporary or parent.temporary,
        )

    def __evict(self):
        # Todo: Evict temporary configs after a while.
        pass

    def __str__(self) -> str:
        return (
            f"Override(permanent={self.permanent}, temporary={self.temporary})"
        )


class Config:
    "A relative configuration for an abstract light."

    def __init__(
        self,
        colorful:       Override[bool]  = Override.none(),
        dynamic:        Override[bool]  = Override.none(),
        toggled_on:     Override[bool]  = Override.none(),
        brightness_mod: Override[float] = Override.none(),
        white_temp_mod: Override[float] = Override.none(),
        color_offset:   Override[int]   = Override.none(),
        static:         Override[State] = Override.none(),
    ):
        self._colorful:       Override[bool]  = colorful
        self._dynamic:        Override[bool]  = dynamic
        self._toggled_on:     Override[bool]  = toggled_on
        self._brightness_mod: Override[float] = brightness_mod
        self._white_temp_mod: Override[float] = white_temp_mod
        self._color_offset:   Override[int]   = color_offset
        self._static:         Override[State] = static

    @property
    def colorful(self) -> Override[bool]:
        "Returns the respective override object."
        return self._colorful

    @property
    def dynamic(self) -> Override[bool]:
        "Returns the respective override object."
        return self._dynamic

    @property
    def toggled_on(self) -> Override[bool]:
        "Returns the respective override object."
        return self._toggled_on

    @property
    def brightness_mod(self) -> Override[float]:
        "Returns the respective override object."
        return self._brightness_mod

    @property
    def white_temp_mod(self) -> Override[float]:
        "Returns the respective override object."
        return self._white_temp_mod

    @property
    def color_offset(self) -> Override[int]:
        "Returns the respective override object."
        return self._color_offset

    @property
    def static(self) -> Override[State]:
        "Returns the respective override object."
        return self._static

    def with_parent(self, parent: 'Config') -> 'Config':
        "Creates a configuration with self's overrides if present, otherwise parent's."
        return Config(
            colorful       = self.colorful.with_parent(       parent.colorful       ),
            dynamic        = self.dynamic.with_parent(        parent.dynamic        ),
            toggled_on     = self.toggled_on.with_parent(     parent.toggled_on     ),
            brightness_mod = self.brightness_mod.with_parent( parent.brightness_mod ),
            white_temp_mod = self.white_temp_mod.with_parent( parent.white_temp_mod ),
            color_offset   = self.color_offset.with_parent(   parent.color_offset   ),
            static         = self.static.with_parent(         parent.static         ),
        )

    def __str__(self):
        res = f"Col: {self.colorful.value}; "
        res += f"dyn: {self.dynamic.value}; "
        res += f"dyn: {self.toggled_on.value}; "
        res += f"brigh: {self.brightness_mod.value}; "
        res += f"colδ: {self.color_offset.value}; "
        res += f"static: {self.static.value}."
        return res

def resolve(cfg: Config, dynamic: State) -> State:
    "Returns the appropriate state of the dynamic state and given config."
    if not cfg.dynamic.value_or(alt=True):
        return cfg.static.value_or(alt=State.max())
    dynamic.brightness = scale_relative(
        value=dynamic.brightness,
        scale=cfg.brightness_mod.value_or(alt=0)
    )
    if dynamic.brightness < 0.001:
        dynamic.brightness = 0
    dynamic.white_temp = scale_relative(
        value=dynamic.white_temp,
        scale=cfg.white_temp_mod.value_or(alt=0)
    )
    dynamic.color.hue  += cfg.color_offset.value_or(alt=0) * 0.2
    dynamic.toggled_on = cfg.toggled_on.value_or(dynamic.toggled_on) and dynamic.brightness > 0.0
    if not cfg.colorful.value_or(alt=True):
        dynamic.color = Color("White")
    return dynamic
