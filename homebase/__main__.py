"""
Main module for the smart home.
Starts the controller, handles requests, and listens to a port for commands.
"""

import os
import threading
import time
from queue import Queue
from typing import List

from api.api import Api
from controller import Controller, Refresher
from home.home import Home
from web_api import WebAPI
from worker import Worker

import common

if __name__ == "__main__":
    log_dir = common.config["log"]
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    home = Home()
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

    while True:
        time.sleep(600)
        for idx, (worker, thread) in enumerate(zipped):
            if not thread.is_alive():
                zipped[idx] = (worker, threading.Thread(target=worker.run, args=()))
                zipped[idx][1].start()
