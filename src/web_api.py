"Bla"
import time
import urllib.parse as url
from typing import Optional, Tuple, Dict
from socketserver import TCPServer
from http.server import BaseHTTPRequestHandler
from queue import Queue
from enums import ApiCommand, ApiQuery, HomeBaseError
from queue_data import QData, QDataKind
from topic import Topic
import common
from log import alert

class Handler(BaseHTTPRequestHandler):
    "Handles web requests and issues the required commands over the queue."

    queue: Optional[Queue[QData]] = None

    def __parse_path(self) -> Optional[Tuple[str, str, Dict[str, str]]]:
        parsed = url.urlparse(self.path)
        split = parsed.path.split('/')
        if len(split) != 3 or split[0] != '':
            print("Length of path is not 3 or the first entry is not empty.")
            return None
        kind = split[1]
        command = split[2]
        query = url.parse_qs(parsed.query)
        if "topic" not in query or len(query["topic"]) == 0:
            print(f"Query: {query}")
            return None
        payload: Dict[str, str] = { }
        for key, values in query.items():
            payload[key] = values[0]
        return (kind, command, payload)

    # pylint: disable=invalid-name
    def do_GET(self):
        "Handles GET requests."
        print("GET: " + self.path)
        try:
            parsed = self.__parse_path()
            if parsed is None:
                print("Parsing failed.")
                self.__reply_err()
                return
            (kind, command, query) = parsed
            topic = Topic.from_str(query["topic"])
            print("Command targets " + topic.string)
            if kind == 'command':
                self.__handle_command(command=command, topic=topic, payload=query)
                return
            if kind == 'query':
                self.__handle_query(query_str=command, topic=topic)
                return
        except HomeBaseError as e:
            if common.config["crash_on_error"]:
                raise e
            alert(str(e))

    def __reply_err(self):
        self.send_response(401)
        self.end_headers()

    def __reply_succ(self):
        self.send_response(200)
        self.end_headers()

    def __handle_query(self, query_str: str, topic: Topic):
        if Handler.queue is None:
            raise HomeBaseError.Unreachable
        query = ApiQuery.from_str(query_str)
        if query is None:
            self.__reply_err()
            return
        response_queue = Queue()
        Handler.queue.put(QData.api_query(
            topic=topic,
            query=query,
            response=response_queue
        ))
        self.send_response(200)
        self.end_headers()
        resp = response_queue.get(block=True, timeout=3)
        print(resp)
        self.wfile.write(str.encode(resp))
        return

    def __handle_command(self, command: str, topic: Topic, payload: Dict[str, str]):
        if Handler.queue is None:
            raise HomeBaseError.Unreachable
        cmd = ApiCommand.from_str(command)
        if cmd is None:
            print("Cannot determine cmd")
            self.__reply_err()
            return
        Handler.queue.put(QData(
            kind=QDataKind.ApiAction,
            topic=topic,
            command=cmd,
            payload=payload
        ))
        print("Success")
        self.__reply_succ()
        return

def _update_handler_queue(queue: Queue[QData]):
    "Sets the static queue of the handler class."
    Handler.queue = queue

class WebAPI:
    "Represents the web api of the smart home"
    def __init__(self, queue: Queue[QData]):
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
