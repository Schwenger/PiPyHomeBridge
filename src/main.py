"Main module for the smart home. Starts the controller and listens to a port for commands."

import threading
import os
from queue import Queue
from controller import Controller
import common
from web_api import WebAPI

if __name__ == "__main__":
    log_dir = common.config["log"]
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    ip = common.config["mosquitto"]["ip"]
    port = common.config["mosquitto"]["port"]
    queue = Queue()
    ctrl = Controller(ip, int(port), queue)
    # threading.Thread(target=ctrl.run, args=()).start()
    threading.Thread(target=ctrl.refresh_periodically, args=()).start()
    threading.Thread(target=WebAPI, args=(queue,)).start()
    ctrl.run()
    # while True:
    #     time.sleep(600)
