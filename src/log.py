"Logging logic."

INFO = False
ALERT = True
TRACE = False

def trace(name: str, fun: str, cls: str = ""):
    "Traces function calls."
    if not TRACE:
        return
    if cls != "":
        cls = "(" + cls + ") "
    print(name + " " + cls + fun)

def info(msg: str):
    "Prints an info"
    if not INFO:
        return
    print(msg)

def alert(msg: str):
    "Prints a warning"
    if not ALERT:
        return
    print("****WARNING****")
    print(msg)
