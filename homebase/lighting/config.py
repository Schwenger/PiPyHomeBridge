"Configures an abstract light."

from datetime import datetime as Timestamp
from typing import Generic, Optional, Tuple, TypeVar

from colour import Color
from common import scale_relative
import lighting

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


class Modifier:
    "Contains modifications for light values; relative."
    def __init__(
        self,
        brightness_mod: float = 0.0,  # ∈ [-1.0, +1.0]
        white_temp_mod: float = 0.0,  # ∈ [-1.0, +1.0]
        color_offset:   int   = 0,    # ∈ {0, 1, 2, 3, 4 5}
    ):
        self.brightness_mod   = brightness_mod
        self.white_temp_mod   = white_temp_mod
        self.color_offset = color_offset

    def with_parent(self, parent: 'Modifier') -> 'Modifier':
        "Keeps the current value if present, otherwise the parent's."
        return Modifier(
            brightness_mod=self.brightness_mod or parent.brightness_mod,
            white_temp_mod=self.white_temp_mod or parent.white_temp_mod,
            color_offset=self.color_offset or parent.color_offset,
        )

    def apply_to(self, state: lighting.State) -> lighting.State:
        "Applies the modifier to the state."
        brightness = scale_relative(value=state.brightness, scale=self.brightness_mod)
        white_temp = scale_relative(value=state.white_temp, scale=self.white_temp_mod)
        color = state.color
        color.hue += 0.2 * self.color_offset
        return lighting.State(
            toggled_on=state.toggled_on and brightness > 0,
            brightness=brightness,
            white_temp=white_temp,
            color=color,
        )

    def __str__(self) -> str:
        return (
            f"brightness_mod={self.brightness_mod}\n"
            f"white_temp_mod={self.white_temp_mod}\n"
            f"color_offset={self.color_offset}\n"
        )


class Overrides:
    "A collection of overrides of absolute values."
    def __init__(
        self,
        colorful: Override[bool]  = Override.none(),
        dynamic:  Override[bool]  = Override.none(),
        state:    Override[lighting.State] = Override.none(),
    ):
        self.colorful = colorful
        self.dynamic  = dynamic
        self.state    = state

    def with_parent(self, parent: 'Overrides') -> 'Overrides':
        "Keeps the current value if present, otherwise the parent's."
        return Overrides(
            colorful=self.colorful.with_parent(parent.colorful),
            dynamic=self.dynamic.with_parent(parent.dynamic),
            state=self.state.with_parent(parent.state),
        )

    def __str__(self) -> str:
        return (
            f"Colorful: {self.colorful}\n"
            f"Dynamic: {self.dynamic}\n"
            f"lighting.State: {self.state}\n"
        )

class Absolutes:
    "Contains light configuration values; absolute."
    def __init__(self, colorful: bool, dynamic: bool, state: lighting.State):
        self.colorful = colorful
        self.dynamic = dynamic
        self.state = state

    def __str__(self) -> str:
        return f"colorful={self.colorful}, dynamic={self.dynamic}, state={self.state}"

class Config:
    "A full configuration for a light."
    def __init__(
        self,
        relative: Optional[Modifier]  = None,
        absolute: Optional[Overrides] = None,
    ):
        self.relative = relative or Modifier()
        self.absolute = absolute or Overrides()

    def with_parent(self, parent: 'Config') -> 'Config':
        "Keeps the current value if present, otherwise the parent's."
        return Config(
            relative=self.relative.with_parent(parent.relative),
            absolute=self.absolute.with_parent(parent.absolute),
        )

    def __str__(self) -> str:
        return (
            f"Relative: {self.relative}\n"
            f"Absolute: {self.absolute}\n"
        )

class RootConfig:
    "A fully defined configuration typically specified as root."

    def __init__(self, colorful: bool, dynamic: bool, static: lighting.State):
        self.colorful = colorful
        self.dynamic = dynamic
        self.static = static

    def overridden_by(self, overrides: Overrides) -> 'RootConfig':
        "Applies the overrides to the root configuration."
        static = self.static
        if overrides.state.value is not None:
            static = overrides.state.value
        colorful = self.colorful
        if overrides.colorful.value is not None:
            colorful = overrides.colorful.value
        dynamic = self.dynamic
        if overrides.dynamic.value is not None:
            dynamic = overrides.dynamic.value
        return RootConfig(static=static, colorful=colorful, dynamic=dynamic)

    def __str__(self) -> str:
        return (
            f"Colorful: {self.colorful}\n"
            f"Dynamic: {self.dynamic}\n"
            f"Static: {self.static}\n"
        )

def resolve(root: RootConfig, override: Config, dynamic: lighting.State) -> lighting.State:
    "Applies the configuration to the root configuration and returns the appropriate state."
    config: RootConfig = root.overridden_by(override.absolute)
    state: lighting.State = dynamic if config.dynamic else config.static
    res = override.relative.apply_to(state)

    if not config.colorful:
        res.white_temp = 1 if state.toggled_on else 0
        res.color = Color("White")

    return res
