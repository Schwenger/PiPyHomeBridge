"Configures an abstract light."

from datetime import datetime as Timestamp
from typing import Generic, Optional, Tuple, TypeVar

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
        # Todo: Evict temporary configs after a while.
        if self.temporary is not None:
            return self.temporary[0]
        return self.permanent

    def value_or(self, alt: T) -> T:
        "Provides the permanent or overriden value if any"
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

    def set_permanent(self, pval: T):
        "Sets the permanent override value."
        self.permanent = pval

    def with_parent(self, parent: 'Override[T]') -> 'Override[T]':
        "Returns an override with the own property if present, otherwise the parent's."
        return Override(
            permanent=self.permanent or parent.permanent,
            temporary=self.temporary or parent.temporary,
        )

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
        brightness_mod: Override[float] = Override.none(),
        white_temp_mod: Override[float] = Override.none(),
        color_offset:   Override[int]   = Override.none(),
        static:         Override[State] = Override.none(),
    ):
        self.colorful:       Override[bool]  = colorful
        self.dynamic:        Override[bool]  = dynamic
        self.brightness_mod: Override[float] = brightness_mod
        self.white_temp_mod: Override[float] = white_temp_mod
        self.color_offset:   Override[int]   = color_offset
        self.static:         Override[State] = static

    def with_parent(self, parent: 'Config') -> 'Config':
        "Creates a configuration with self's overrides if present, otherwise parent's."
        return Config(
            colorful       = self.colorful.with_parent(       parent.colorful       ),
            dynamic        = self.dynamic.with_parent(        parent.dynamic        ),
            brightness_mod = self.brightness_mod.with_parent( parent.brightness_mod ),
            white_temp_mod = self.white_temp_mod.with_parent( parent.white_temp_mod ),
            color_offset   = self.color_offset.with_parent(   parent.color_offset   ),
            static         = self.static.with_parent(         parent.static         ),
        )

def resolve(cfg: Config, dynamic: State) -> State:
    "Returns the appropriate state of the dynamic state and given config."
    if not cfg.dynamic.value_or(alt=False):
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
    dynamic.toggled_on = dynamic.toggled_on and dynamic.brightness > 0
    if not cfg.colorful.value_or(alt=False):
        dynamic.color = Color("White")
    return dynamic
