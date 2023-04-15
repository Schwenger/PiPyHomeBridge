"""
Main module for the smart home.
Starts the controller, handles requests, and listens to a port for commands.
"""

import threading
import time
from queue import Queue
from typing import List

import common
from api.api import Api
from controller import Controller, Refresher
from home import decoder
from web_api import WebAPI
from worker import Worker

if __name__ == "__main__":

    home = decoder.read(common.config["home"]["dir"])
    # from home import encoder
    # encoder.write(home, "/Users/schwenger/Workspace/smart_home/config/home.out.yml")

    cmd_q = Queue()
    resp_q = Queue()

    ctrl      = Controller(cmd_q, home)
    refresher = Refresher(cmd_q)
    web       = WebAPI(cmd_q, resp_q)
    api       = Api(request_q=cmd_q, response_q=resp_q, home=home, client=ctrl.client)

    workers: List[Worker] = [ctrl, api, refresher, web]
    threads: List[threading.Thread] = []

    for worker in workers:
        thread = threading.Thread(target=worker.run, args=())
        threads.append(thread)
        thread.start()

    zipped = list(zip(workers, threads))

    # import json
    # time.sleep(2)
    # pl = {"state": "ON", "color": { "saturation": 100, "hue": 240} }
    # ctrl.client.publish('zigbee2mqtt/Device/Light/Living Room/Orb/set', json.dumps(pl))
    # print("Published")

    while True:
        time.sleep(600)
        for idx, (worker, thread) in enumerate(zipped):
            if not thread.is_alive():
                zipped[idx] = (worker, threading.Thread(target=worker.run, args=()))
                zipped[idx][1].start()
