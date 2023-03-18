"Logging logic."

from datetime import datetime
import common

INFO = True
ALERT = True
TRACE = True

PATH = common.config['log']
LOG_TO_FILE = common.config['log_to_file']


def trace(name: str, fun: str, cls: str = ""):
    "Traces function calls."
    if not TRACE:
        return
    if cls != "":
        cls = "(" + cls + ") "
    _put(name + " " + cls + fun)


def info(msg: str):
    "Prints an info"
    if not INFO:
        return
    _put(msg)


def alert(msg: str):
    "Prints a warning"
    if not ALERT:
        return
    _put("****WARNING****")
    _put(msg)


def client(topic: str, payload: str):
    "Prints info about a published message"
    _put(f"{datetime.now()}: Publish {payload} to {topic}", target="client")


def web_request(path: str):
    "Prints infor about a web request"
    _put(f"{datetime.now()}: Request to {path}", target="webapi")


def qdata(data: str):
    "Prints infor about a web request"
    _put(f"{datetime.now()}: QData for {data}", target="qdata")


def report_error(err: Exception, src: str):
    "Handles any error."
    if common.config["crash_on_error"]:
        raise err
    alert(f"{src}: {err}")


def _put(msg: str, target: str = "main.log"):
    if LOG_TO_FILE:
        with open(PATH + "/" + target + ".log", "a", encoding="utf-8") as file:
            file.write(msg + "\n")
    else:
        print(msg)
