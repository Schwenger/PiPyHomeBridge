"A module for common functionality"

import platform
import yaml

NODE_NAME = platform.node()
if 'Mairxbook' in NODE_NAME:
    CLIENT_NAME = 'Mac'
else:
    CLIENT_NAME = 'Pi'

with open("config.yml", "r", encoding="utf-8") as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print("Failed to load config file config.yml.")
        raise exc
