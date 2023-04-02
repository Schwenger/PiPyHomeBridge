"Configures an abstract light."

from datetime import datetime as Timestamp
from typing import Callable, Generic, Optional, Tuple, TypeVar

from colormath.color_objects import HSVColor
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
        hue:            Override[float] = Override.none(),
        saturation:     Override[float] = Override.none(),
        lumin:          Override[float] = Override.none(),
        static:         Override[State] = Override.none(),
    ):
        self._colorful:       Override[bool]  = colorful
        self._dynamic:        Override[bool]  = dynamic
        self._toggled_on:     Override[bool]  = toggled_on
        self._hue:            Override[float] = hue
        self._saturation:     Override[float] = saturation
        self._lumin:          Override[float] = lumin
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
    def hue(self) -> Override[float]:
        "Returns the respective override object."
        return self._hue

    @property
    def saturation(self) -> Override[float]:
        "Returns the respective override object."
        return self._saturation

    @property
    def lumin(self) -> Override[float]:
        "Returns the respective override object."
        return self._lumin

    @property
    def static(self) -> Override[State]:
        "Returns the respective override object."
        return self._static

    def with_parent(self, parent: 'Config') -> 'Config':
        "Creates a configuration with self's overrides if present, otherwise parent's."
        return Config(
            colorful   = self.colorful.with_parent(   parent.colorful   ),
            dynamic    = self.dynamic.with_parent(    parent.dynamic    ),
            toggled_on = self.toggled_on.with_parent( parent.toggled_on ),
            hue        = self.hue.with_parent(        parent.hue        ),
            saturation = self.saturation.with_parent( parent.saturation ),
            lumin      = self.lumin.with_parent(      parent.lumin      ),
            static     = self.static.with_parent(     parent.static     ),
        )

    def __str__(self):
        res = f"Col: {self.colorful.value}; "
        res += f"dyn: {self.dynamic.value}; "
        res += f"on/off: {self.toggled_on.value}; "
        res += f"""color: \
{(self.hue.value or 0.0):.2f}/\
{(self.saturation.value or 0.0):.2f}/\
{(self.lumin.value or 0.0):.2f};"""
        res += f"static: {self.static.value}"
        return res

def resolve(cfg: Config, dynamic: State) -> State:
    "Returns the appropriate state of the dynamic state and given config."
    if not cfg.dynamic.value_or(alt=True):
        state = cfg.static.value_or(alt=State.max())
        state.toggled_on = cfg.toggled_on.value_or(state.toggled_on)
        return state
    dynamic.color = __adapt_color(dynamic.color, cfg)
    dynamic.toggled_on = cfg.toggled_on.value_or(dynamic.toggled_on) and dynamic.color.hsv_v > 0.0
    if not cfg.colorful.value_or(alt=True):
        dynamic.color = HSVColor(1, 0, 1)
    return dynamic

def __adapt_color(col: HSVColor, cfg: Config) -> HSVColor:
    val = scale_relative(value=col.hsv_v, scale=cfg.lumin.value_or(alt=0))
    sat = scale_relative(value=col.hsv_s, scale=cfg.saturation.value_or(alt=0))
    hue = scale_relative(value=col.hsv_h, scale=cfg.hue.value_or(alt=0))
    if val < 0.001:
        val = 0
    assert 0 <= val <= 1
    assert 0 <= sat <= 1
    assert 0 <= hue <= 1
    return HSVColor(hsv_v=val, hsv_h=hue, hsv_s=sat)
