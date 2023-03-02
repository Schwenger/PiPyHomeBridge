"Main module for the smart home. Starts the controller and listens to a port for commands."

import threading
import time
from queue import Queue
from controller import Controller
import common
# from portlistener import WebAPI

if __name__ == "__main__":
    ip = common.config["mosquitto"]["ip"]
    port = common.config["mosquitto"]["port"]
    queue = Queue()
    ctrl = Controller(ip, int(port), queue)
    threading.Thread(target=ctrl.run, args=()).start()
    threading.Thread(target=ctrl.refresh_periodically, args=()).start()
    # threading.Thread(target=WebAPI, args=(queue,)).start()
    while True:
        time.sleep(600)
