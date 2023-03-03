"Bla"
from typing import Optional
from socketserver import TCPServer
from http.server import BaseHTTPRequestHandler
from queue import Queue
from enums import ApiCommand
from queue_data import QData, QDataKind
from topic import Topic

class Handler(BaseHTTPRequestHandler):
    "Handles web requests and issues the required commands over the queue."
    queue: Optional[Queue] = None
    # pylint: disable=invalid-name
    def do_GET(self):
        "Handles GET requests."
        print("Received request: " + self.path)
        assert Handler.queue is not None
        split = self.path.split('/')
        if len(split) != 2 or split[0] != '':
            print("Sending error response.")
            self.send_response(401)
            self.end_headers()
            return
        cmd = ApiCommand.from_str(split[1])
        if cmd is None:
            print("Sending error response.")
            self.send_response(401)
            self.end_headers()
            return
        topic = Topic(device="", room="Living Room", name="")
        Handler.queue.put(QData(kind=QDataKind.ApiAction, topic=topic, command=cmd))
        print("Sending positive response.")
        self.send_response(200)
        self.end_headers()

def _update_handler_queue(queue: Queue):
    "Sets the static queue of the handler class."
    Handler.queue = queue

class WebAPI:
    "Represents the web api of the smart home"
    def __init__(self, queue: Queue):
        print("Initializing WebAPI")
        _update_handler_queue(queue)
        httpd = TCPServer(("", 8080), Handler)
        httpd.serve_forever()
