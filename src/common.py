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
with open(cfg_path, "r", encoding="utf-8") as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print("Failed to load config file config.yml.")
        raise exc
