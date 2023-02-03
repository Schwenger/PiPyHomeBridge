"Logging logic."

INFO = False
ALERT = True
TRACE = False

WRITE_TO_FILE = True

PATH = '/home/pi/log'

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

def _put(msg: str):
    if WRITE_TO_FILE:
        with open(PATH, "a", encoding="utf-8") as file:
            file.write(msg)
    else:
        print(msg)
