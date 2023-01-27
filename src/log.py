"Logging logic."

INFO = True
WARN = True
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

def warn(msg: str):
    "Prints a warning"
    if not WARN:
        return
    print("****WARNING****")
    print(msg)
