"Collection of all expected errors."

from enum import Enum

# pylint: disable=invalid-name
class HomeBaseError(Exception, Enum):
    "General error class"
    PayloadNotFound = "Could not find a they required payload."
    RoomNotFound = "Could not find room."
    RemoteNotFound = "Could not find remote."
    Unreachable = "Some programmer error occured."
    DeviceNotFound = "Could not find device."
    InvalidRemoteAction = "Cannot determine the action of a remote operation."
    TopicParseError = "Failed to parse remote string."
    WebRequestParseError = "Failed to parse URL of web request."
    QueryNoResponse = "Did not receive a response for a query in time."
    InvalidPhysicalQuery = "Query target is not a valid physical device."
    InvalidPhysicalQuantity = "Cannot transform the given quantity into a float."
