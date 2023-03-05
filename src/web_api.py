"Bla"
import time
import urllib.parse as url
from typing import Optional, Tuple
from socketserver import TCPServer
from http.server import BaseHTTPRequestHandler
from queue import Queue
from enums import ApiCommand, ApiQuery
from queue_data import QData, QDataKind
from topic import Topic

class Handler(BaseHTTPRequestHandler):
    "Handles web requests and issues the required commands over the queue."

    queue: Optional[Queue] = None

    def __parse_path(self) -> Optional[Tuple[str, str, Topic]]:
        parsed = url.urlparse(self.path)
        split = parsed.path.split('/')
        if len(split) != 3 or split[0] != '':
            return None
        kind = split[1]
        command = split[2]
        query = url.parse_qs(parsed.query)
        if "topic" not in query or len(query["topic"]) == 0:
            return None
        topic_str = query["topic"][0]
        return (kind, command, Topic.from_str(topic_str))

    # pylint: disable=invalid-name
    def do_GET(self):
        "Handles GET requests."
        print("GET: " + self.path)
        parsed = self.__parse_path()
        if parsed is None:
            print("Parsing failed.")
            self.__reply_err()
            return
        (kind, command, topic) = parsed
        if kind == 'command':
            self.__handle_command(command=command, topic=topic)
            return
        if kind == 'query':
            self.__handle_query(query_str=command, topic=topic)
            return

    def __reply_err(self):
        self.send_response(401)
        self.end_headers()

    def __reply_succ(self):
        self.send_response(200)
        self.end_headers()

    def __handle_query(self, query_str: str, topic: Optional[Topic]):
        query = ApiQuery.from_str(query_str)
        if query is None:
            self.__reply_err()
            return
        topic = topic or Topic.for_room("Living Room")
        response_queue = Queue()
        assert Handler.queue is not None
        Handler.queue.put(QData.api_query(
            topic=topic,
            query=query,
            response=response_queue
        ))
        self.send_response(200)
        self.end_headers()
        resp = response_queue.get(block=True)
        print(resp)
        self.wfile.write(str.encode(resp))
        return

    def __handle_command(self, command: str, topic: Optional[Topic]):
        cmd = ApiCommand.from_str(command)
        if cmd is None:
            print("Cannot determine cmd")
            self.__reply_err()
            return
        topic = topic or Topic.for_room("Living Room")
        assert Handler.queue is not None
        Handler.queue.put(QData(
            kind=QDataKind.ApiAction,
            topic=topic,
            command=cmd
        ))
        print("Success")
        self.__reply_succ()
        return

def _update_handler_queue(queue: Queue):
    "Sets the static queue of the handler class."
    Handler.queue = queue

class WebAPI:
    "Represents the web api of the smart home"
    def __init__(self, queue: Queue):
        _update_handler_queue(queue)
        for retry in range(10):
            try:
                httpd = TCPServer(("", 8088), Handler)
                httpd.serve_forever()
            except OSError as ose:
                print(f"Failed attempt to bind socket. Retry: {retry}.")
                if retry == 9:
                    raise ose
            time.sleep(1)
