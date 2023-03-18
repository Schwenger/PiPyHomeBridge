"A module for common functionality"

import platform
import os
import yaml

NODE_NAME = platform.node()
if 'Mairxbook' in NODE_NAME:
    CLIENT_NAME = 'Mac'
else:
    CLIENT_NAME = 'Pi'

base_path = os.path.dirname(os.path.realpath(__file__))
cfg_path = os.path.join(base_path, '..', 'config.yml')
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
