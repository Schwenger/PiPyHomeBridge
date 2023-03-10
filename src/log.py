"Logging logic."

from typing import Optional
from datetime import datetime
import common

INFO = False
ALERT = True
TRACE = False

PATH = common.config['log']
WRITE_TO_FILE = PATH != ''

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

def log_web_request(path: str):
    "Prints infor about a web request"
    _put(f"{datetime.now()}: Request to {path}", target="webapi.log")

def log_qdata(qdata: str):
    "Prints infor about a web request"
    _put(f"{datetime.now()}: QData for {qdata}", target="qdata.log")

def _put(msg: str, target: Optional[str] = None):
    if target is not None:
        with open("log/" + target, "a", encoding="utf-8") as file:
            file.write(msg + "\n")
    elif WRITE_TO_FILE:
        with open(PATH, "a", encoding="utf-8") as file:
            file.write(msg + "\n")
    else:
        print(msg)
