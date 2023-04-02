"A module containing common functionality for API-modules."

from typing import Optional

import lighting
import lighting.config
from comm import Topic
from common import Log
from home import Home
from homebaseerror import HomeBaseError
from sensor import Sensor


def get_abstract(topic: Topic, home: Home) -> Optional[lighting.Abstract]:
    "Returns the abstract light with the given topic, if it exists within home."
    conc = home.find_light(topic)
    if conc is not None:
        return conc
    for room in home.rooms:
        if topic in [room.group.topic, room.topic]:
            return room.group
    return None

def get_abstract_force(topic: Topic, home: Home) -> lighting.Abstract:
    "Returns the abstract light with the given topic, raises Exception otherwise."
    res = get_abstract(topic, home)
    if res is None:
        Log.api.error("Cannot find device for %s", topic.string)
        raise HomeBaseError.DeviceNotFound
    return res

def get_sensor(topic: Topic, home: Home) -> Optional[Sensor]:
    "Returns the sensor with the given topic, if it exists within home."
    return home.find_sensor(topic)

def get_configured_state(home: Home, light: lighting.Abstract) -> lighting.State:
    "Returns the currently relevant state for the current config of the light."
    dynamic = lighting.dynamic.recommended()
    Log.api.debug(dynamic)
    config = home.compile_config(light.topic)
    Log.api.debug(config)
    assert config is not None
    target = lighting.config.resolve(config, dynamic)
    Log.api.debug(target)
    return target
