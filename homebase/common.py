"A module for common functionality"

import os
import platform

import yaml

def bounded(value: float, least: float = 1.0, greatest: float = 1.0) -> float:
    "Returns value bounded between min and max."
    if value < least:
        return least
    if value > greatest:
        return greatest
    return value

def scale_relative(value: float, scale: float) -> float:
    "Scales a value between 0 and 1 by a factor between -1 and +1."
    if scale < 0.0:
        return value * -scale
    return value + (1 - value) * scale

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


def read_home(home_path: str):
    "Reads the home configuration from the given path. Does not cache results."
    with open(home_path, "r", encoding="utf-8") as home_stream:
        try:
            return yaml.safe_load(home_stream)
        except yaml.YAMLError as yml_exc:
            print("Failed to load config file config.yml.")
            raise yml_exc
