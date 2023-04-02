"A module for common functionality"

import os
import platform
import logging
from typing import Optional

import yaml


def bounded(value: float, bounds: range = range(-1, 1)) -> float:
    "Returns value bounded between min and max."
    least = float(bounds.start)
    greatest = float(bounds.stop)
    if value < least:
        return least
    if value > greatest:
        return greatest
    return value

def scale_relative(value: float, scale: float) -> float:
    "Scales a value between 0 and 1 by a factor between -1 and +1."
    if scale < 0.0:
        return value * (1 + scale)
    # Caution: Changes here must result in changes in engineer_modifier!
    return value + scale * (1 - value)

def engineer_modifier(actual: float, desired: float) -> float:
    "Returns the factor required to transform actual to desired."
    if desired == actual:
        return 0
    if desired > actual:
        # actual < desired -> scale > 0
        # actual + λ(1-actual) = desired
        # λ(1-actual) = desired - actual
        # λ = (desired-actual)/(1-actual)
        # Denominator cannot be 0 because if actual were 1, desired couldn't be strictly greater.
        return (desired - actual) / (1 - actual)
    # actual > desired -> scale < 0
    # actual * (1+λ) = desired
    # 1+λ = desired/actual
    # λ = desired/actual-1
    # Denominator cannot be 0 because if actual were 0, since it must be >= desired,
    # desired would also be 0, which is handled in a separate case.
    return desired/actual - 1

NODE_NAME = platform.node()
if 'Mairxbook' in NODE_NAME:
    CLIENT_NAME = 'Mac'
else:
    CLIENT_NAME = 'Pi'

base_path = os.path.dirname(os.path.realpath(__file__))
cfg_path = os.path.join(base_path, '..', 'config', 'config.yml')
config = {}
with open(cfg_path, "r", encoding="utf-8") as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print("Failed to load config file config.yml.")
        raise exc

class Log:
    "Collection of viable logs"
    web = logging.getLogger("Web")
    api = logging.getLogger("Api")
    rfs = logging.getLogger("Rfs")
    ctl = logging.getLogger("Ctl")
    tpc = logging.getLogger("Tpc")
    utl = logging.getLogger("Utl")

Log.web.setLevel(logging.INFO)
Log.api.setLevel(logging.DEBUG)
Log.rfs.setLevel(logging.INFO)
Log.ctl.setLevel(logging.INFO)
logging.getLogger().setLevel(logging.ERROR)  # color uses this logger :roll_eyes:

log_dir = config["log"]["dir"]

if not os.path.exists(log_dir):
    os.mkdir(log_dir)

log_fmt = config["log"]["format"]

logging.basicConfig(
    filename=os.path.join(log_dir, 'mylogs.log'),
    format=log_fmt,
    datefmt='%d/%H:%M:%S'
)

def read_home(home_path: str):
    "Reads the home configuration from the given path. Does not cache results."
    with open(home_path, "r", encoding="utf-8") as home_stream:
        try:
            return yaml.safe_load(home_stream)
        except yaml.YAMLError as yml_exc:
            print("Failed to load config file config.yml.")
            raise yml_exc
