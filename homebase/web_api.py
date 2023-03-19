"Bla"
import urllib.parse as url
from typing import Optional, Tuple, Dict
from socketserver import TCPServer
from http.server import BaseHTTPRequestHandler
from queue import Queue, Empty
from enums import ApiCommand, ApiQuery, HomeBaseError
from queue_data import QData, QDataKind
from home.topic import Topic
from worker import Worker
import log


class Handler(BaseHTTPRequestHandler):
    "Handles web requests and issues the required commands over the queue."

    request:  Optional[Queue] = None
    response: Optional[Queue] = None

    # pylint: disable=invalid-name
    def do_GET(self):
        "Handles GET requests."
        try:
            log.web_request(self.path)
            self.__handle_request()
        except Exception as err:
            log.report_error(err, src="WebApi")
            self.send_response(401)
            self.end_headers()

    def __handle_request(self):
        parsed = self.__parse_path()
        if parsed is None:
            log.alert("Parsing request failed: " + self.path)
            raise HomeBaseError.WebRequestParseError
        (kind, command, query) = parsed
        topic = Topic.from_str(query["topic"])
        if topic.target == "bridge":
            log.alert("Received a bridge-targetted message over Web API.")
            log.alert(self.path)
            log.alert(command)
            log.alert(str(query))
        if kind == 'command':
            return self.__handle_command(command=command, topic=topic, payload=query)
        elif kind == 'query':
            return self.__handle_query(query_str=command, topic=topic)
        log.alert("Parsing request kind failed: " + kind)
        raise HomeBaseError.WebRequestParseError

    def __parse_path(self) -> Optional[Tuple[str, str, Dict[str, str]]]:
        parsed = url.urlparse(self.path)
        split = parsed.path.split('/')
        if len(split) != 3 or split[0] != '':
            log.alert("Length of path is not 3 or the first entry is not empty.")
            raise HomeBaseError.WebRequestParseError
        kind = split[1]
        command = split[2]
        query = url.parse_qs(parsed.query)
        if "topic" not in query or len(query["topic"]) == 0:
            log.alert("Either there is no topic or the topic is empty.")
            raise HomeBaseError.WebRequestParseError
        payload: Dict[str, str] = { }
        for key, values in query.items():
            payload[key] = values[0]
        return (kind, command, payload)

    def __handle_query(self, query_str: str, topic: Topic):
        if Handler.request is None or Handler.response is None:
            raise HomeBaseError.Unreachable
        query = ApiQuery.from_str(query_str)
        if query is None:
            log.alert("Query does not contain a valid command: " + str(query))
            raise HomeBaseError.WebRequestParseError
        Handler.request.put(QData.api_query(
            topic=topic,
            query=query
        ))
        self.send_response(200)
        self.end_headers()
        try:
            resp = Handler.response.get(block=True, timeout=60)
        except Empty as ecx:
            log.alert("Did not get a response within 60 seconds.")
            raise HomeBaseError.QueryNoResponse from ecx
        log.info("Responding to query with:")
        log.info(resp)
        self.wfile.write(str.encode(resp))
        return

    def __handle_command(self, command: str, topic: Topic, payload: Dict[str, str]):
        if Handler.request is None:
            raise HomeBaseError.Unreachable
        cmd = ApiCommand.from_str(command)
        if cmd is None:
            log.alert("Command does not contain a valid command: " + str(command))
            raise HomeBaseError.WebRequestParseError
        Handler.request.put(QData(
            kind=QDataKind.ApiAction,
            topic=topic,
            command=cmd,
            payload=payload
        ))
        self.send_response(200)
        self.end_headers()
        return


def _update_handler_queue(request: Queue, response: Queue):
    "Sets the static queue of the handler class."
    Handler.request  = request
    Handler.response = response


class WebAPI(Worker):
    "Represents the web api of the smart home"
    def __init__(self, request: Queue, response: Queue):
        _update_handler_queue(request=request, response=response)

    def run(self):
        "Starts serving TCP requests."
        try:
            httpd = TCPServer(("", 8088), Handler)
            httpd.serve_forever()
        except OSError as ose:
            print("Failed attempt to bind socket.")
            raise ose
