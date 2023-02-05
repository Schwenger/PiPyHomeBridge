"Data to be put into the queue."

from enum import Enum
from typing import Optional
from payload import Topic

class Kind(Enum):
    "The kind of data in the queue."
    REFRESH = "Refresh"
    ADDRESSED = "Addressed"
    API = "API"

class Cmd(Enum):
    "A command to be executed."
    QUERY = "Query"

REFRESH = { "kind" : Kind }
def addressed(topic: Topic, data):
    "A message from a remote was received"
    return {
        "kind": Kind.ADDRESSED,
        "topic": topic,
        "data": data,
    }

def api(cmd: Cmd, target: Optional[Topic]):
    "A message from a remote was received"
    res = {
        "kind": Kind.API,
        "cmd": cmd,
    }
    if target is not None:
        res["target"] = target
    return res
