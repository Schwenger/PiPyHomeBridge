"""
An API to play around with commands manually or to code a more user-friendly, python-less interface.
"""

import threading
from payload import Topic
import queue_data as QData
import controller

ctrl = controller.Controller()
ctrl.client.loop_start()

def loop():
    "Loops the controller"
    while True:
        ctrl.loop()

refresh_thread = threading.Thread(target=ctrl.refresh_periodically, args=(ctrl.queue,))
refresh_thread.start()
ctrl_thread = threading.Thread(target=loop, args=())
ctrl_thread.start()


def query_state(topic: Topic):
    "Queries the state of the device with the given topic"
    ctrl.queue.put(QData.api(cmd=QData.Cmd.QUERY, target=topic))

ORB = Topic(room="Living Room", physical_kind="Light", name="Orb")
