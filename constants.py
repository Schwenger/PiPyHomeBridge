"Collection of all relevant constants."

TOPIC_NAME                  = "zigbee2mqtt"
TOPIC_LIVING_ROOM           = TOPIC_NAME        + "/Living Room"
TOPIC_LR_REMOTES            = TOPIC_LIVING_ROOM + "/Remote"
TOPIC_LR_LIGHTS             = TOPIC_LIVING_ROOM + "/Light"
TOPIC_LR_OUTLETS            = TOPIC_LIVING_ROOM + "/Outlet"
TOPIC_LR_REMOTE             = TOPIC_LR_REMOTES  + "/Remote"
TOPIC_LR_COMFORT_LIGHT      = TOPIC_LR_OUTLETS  + "/Comfort Light"
TOPIC_LR_UPLIGHT_MAIN       = TOPIC_LR_LIGHTS   + "/Uplight/Main"
TOPIC_LR_UPLIGHT_READING    = TOPIC_LR_LIGHTS   + "/Uplight/Reading"
TOPICS_UPLIGHT = [TOPIC_LR_UPLIGHT_MAIN, TOPIC_LR_UPLIGHT_READING]
CMD_GET = "/get"
CMD_SET = "/set"
TOGGLE_PAYLOAD  = '{ "state": "TOGGLE" }'
OFF_PAYLOAD     = '{ "state": "OFF" }'
ON_PAYLOAD      = '{ "state": "ON" }'
