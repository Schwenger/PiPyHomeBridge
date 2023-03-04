"Bla"
from typing import Optional
from socketserver import TCPServer
from http.server import BaseHTTPRequestHandler
from queue import Queue
from enums import ApiCommand, ApiQuery
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
        if len(split) != 3 or split[0] != '':
            self.__reply_err()
            return
        if split[1] == 'command':
            cmd = ApiCommand.from_str(split[2])
            if cmd is None:
                self.__reply_err()
                return
            topic = Topic.for_room("Living Room")
            Handler.queue.put(QData(
                kind=QDataKind.ApiAction,
                topic=topic,
                command=cmd
            ))
            self.__reply_succ()
            return
        elif split[1] == 'query':
            query = ApiQuery.from_str(split[2])
            if query is None:
                self.__reply_err()
                return
            topic = Topic.for_room("Living Room")
            response_queue = Queue()
            Handler.queue.put(QData.api_query(
                topic=topic,
                query=query,
                response=response_queue
            ))
            self.send_response(200)
            self.end_headers()
            resp = response_queue.get(block=True)
            self.wfile.write(str.encode(resp))
            return

    def __reply_err(self):
        self.send_response(401)
        self.end_headers()

    def __reply_succ(self):
        self.send_response(200)
        self.end_headers()

def _update_handler_queue(queue: Queue):
    "Sets the static queue of the handler class."
    Handler.queue = queue

class WebAPI:
    "Represents the web api of the smart home"
    def __init__(self, queue: Queue):
        _update_handler_queue(queue)
        httpd = TCPServer(("", 8088), Handler)
        httpd.serve_forever()
