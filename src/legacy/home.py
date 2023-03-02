# "Represents the structure of the smart home from areas down to devices."

# from typing import List
# import common
# from payload import Topic
# from remote import IkeaMultiButton
# from queue_data import LightStateChange
# from lights import LightState

# class Home:
#     "Represents the structure of the smart home from areas down to devices."
#     def __init__(self):
#         self.__structure = common.read_home(common.config["home"])

#     def all_remotes(self) -> List[Topic]:
#         "Returns a list of all remotes"
#         return self.__all_of_a_function("Remote")

#     def all_lights(self) -> List[Topic]:
#         "Returns a list of all lights"
#         return self.__all_of_a_function("Light")

#     def room_by_name(self, name: str) -> str:
#         "Finds the room with the given name."
#         for room in self.__structure["rooms"]:
#             if room["name"] == name:
#                 return room["id"]
#         raise ValueError

#     # def device_by_topic(self, topic: Topic):
#     #     "Finds the device with the given topic."
#     #     room_id = self.room_by_name(topic.room)
#     #     for device in self.__structure["devices"]:
#     #         kind_match = device["kind"] == topic.physical_kind
#     #         name_match = device["name"] == topic.name
#     #         room_match = device["room"] == room_id
#     #         if kind_match and name_match and room_match:
#     #             return device
#     #     raise ValueError

#     # def device_by_id(self, did: str):
#     #     "Finds the device with the given id."
#     #     for device in self.__structure["devices"]:
#     #         if device["id"] == did:
#     #             return device
#     #     raise ValueError

#     # def configured_remote_action(self, _remote: Topic, _action: IkeaMultiButton):
#     #     return LightStateChange(LightState(toggled_on=False))
#         # if action == IkeaMultiButton.TOGGLE:
#         # elif action == IkeaMultiButton.ARR_LEFT_CLICK:
#         # elif action == IkeaMultiButton.ARR_LEFT_HOLD:
#         # elif action == IkeaMultiButton.ARR_LEFT_RELEASE:
#         # elif action == IkeaMultiButton.ARR_RIGHT_CLICK:
#         # elif action == IkeaMultiButton.ARR_RIGHT_HOLD:
#         # elif action == IkeaMultiButton.ARR_RIGHT_RELEASE:
#         # elif action == IkeaMultiButton.BRI_DOWN_CLICK:
#         # elif action == IkeaMultiButton.BRI_DOWN_HOLD:
#         # elif action == IkeaMultiButton.BRI_DOWN_RELEASE:
#         # elif action == IkeaMultiButton.BRI_UP_CLICK:
#         # elif action == IkeaMultiButton.BRI_UP_HOLD:
#         # elif action == IkeaMultiButton.BRI_UP_RELEASE:

#     def __all_of_a_function(self, function: str) -> List[Topic]:
#         devices = self.__structure["devices"]
#         devices = filter(lambda d: d["function"] == function, devices)
#         return list(map(self.__device_to_topic, devices))

#     def __device_to_topic(self, remote) -> Topic:
#         room = self.__room(remote["room"])
#         return Topic(room=room, physical_kind=remote["kind"], name=remote["name"])

#     def __room(self, rid: str) -> str:
#         for room in self.__structure["rooms"]:
#             if room["id"] == rid:
#                 return room["name"]
#         raise ValueError







# # y = 100*e^(-(x - 12.67814)^2/(2*5.491843^2))
