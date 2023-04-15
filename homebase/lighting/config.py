"Configures an abstract light."

import math
from datetime import datetime as Timestamp
from typing import Callable, Generic, Optional, Tuple, TypeVar

from colormath.color_objects import HSVColor
from lighting.state import State
from common import scale_relative, Log, bounded

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
        toggled_on: Override[bool],
        colorful:   Optional[Override[bool]]  = None,
        dynamic:    Optional[Override[bool]]  = None,
        hue:        Optional[Override[float]] = None,
        saturation: Optional[Override[float]] = None,
        lumin_mod:  Optional[Override[float]] = None,
        static:     Optional[Override[State]] = None,
    ):
        self._toggled_on:   Override[bool]  = toggled_on
        self._colorful:     Override[bool]  = colorful    or Override.none()
        self._dynamic:      Override[bool]  = dynamic     or Override.none()
        self._hue:          Override[float] = hue         or Override.none()
        self._saturation:   Override[float] = saturation  or Override.none()
        self._lumin_mod:    Override[float] = lumin_mod   or Override.none()
        self._static:       Override[State] = static      or Override.none()

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
    def lumin_mod(self) -> Override[float]:
        "Returns the respective override object."
        return self._lumin_mod

    @property
    def static(self) -> Override[State]:
        "Returns the respective override object."
        return self._static

    def with_parent(self, parent: 'Config') -> 'Config':
        "Creates a configuration with self's overrides if present, otherwise parent's."
        return Config(
            hue        = self.hue.with_parent(        parent.hue        ),
            lumin_mod  = self.lumin_mod.with_parent(  parent.lumin_mod      ),
            static     = self.static.with_parent(     parent.static     ),
            dynamic    = self.dynamic.with_parent(    parent.dynamic    ),
            colorful   = self.colorful.with_parent(   parent.colorful   ),
            toggled_on = self.toggled_on.with_parent( parent.toggled_on ),
            saturation = self.saturation.with_parent( parent.saturation ),
        )

    def __str__(self):
        res = f"Col: {self.colorful.value}; "
        res += f"dyn: {self.dynamic.value}; "
        res += f"on/off: {self.toggled_on.value}; "
        res += f"""color: \
{(self.hue.value or 0.0):.2f}/\
{(self.saturation.value or 0.0):.2f}/\
{(self.lumin_mod.value or 0.0):.2f};"""
        res += f"static: {self.static.value}"
        return res

def resolve(cfg: Config, dynamic: State) -> State:
    "Returns the appropriate state for the computed dynamic state and given config."
    Log.utl.debug("Resolving config %s with dynamic %s.", cfg, dynamic)
    if not cfg.dynamic.value_or(alt=True):
        Log.utl.debug("Using static state.")
        state = cfg.static.value_or(alt=State.max())
        state.toggled_on = cfg.toggled_on.value_or(state.toggled_on)
        return state
    Log.utl.debug("Using dynamic state")
    dynamic.color = __adapt_color(dynamic.color, cfg)
    dynamic.toggled_on = cfg.toggled_on.value_or(dynamic.toggled_on) and dynamic.color.hsv_v > 0.0
    if not cfg.colorful.value_or(alt=True):
        Log.utl.debug("Erasing color since colorful is off.")
        dynamic.color = HSVColor(1, 0, 1)
    return dynamic

def __adapt_color(col: HSVColor, cfg: Config) -> HSVColor:
    Log.utl.debug("Adapting %s with config %s.", col, cfg)
    val = scale_relative(value=col.hsv_v, scale=cfg.lumin_mod.value_or(alt=0))
    Log.utl.debug("New brightness (value) %s.", val)
    sat = cfg.saturation.value_or(alt=0)
    Log.utl.debug("New saturation %s.", sat)
    hue = cfg.hue.value_or(alt=0)
    Log.utl.debug("New hue %s.", hue)
    if val < 0.05:
        val = 0
    def sanitize(value: float):
        assert value >= 0 or math.isclose(value, 0, abs_tol=1e-4)
        assert value <= 1 or math.isclose(value, 1, abs_tol=1e-4)
        return bounded(value, bounds=range(0, 1))
    val = sanitize(val)
    hue = sanitize(hue)
    sat = sanitize(sat)
    return HSVColor(hsv_v=val, hsv_h=hue, hsv_s=sat)
