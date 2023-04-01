"Bla"
import logging
import urllib.parse as url
from http.server import BaseHTTPRequestHandler
from queue import Empty, Queue
from socketserver import TCPServer
from typing import Dict, Optional, Tuple

from comm import QData, Topic
from enums import ApiCommand, ApiQuery, QDataKind
from homebaseerror import HomeBaseError
from worker import Worker


class Handler(BaseHTTPRequestHandler):
    "Handles web requests and issues the required commands over the queue."

    request:  Optional[Queue] = None
    response: Optional[Queue] = None

    # pylint: disable=invalid-name
    def do_GET(self):
        "Handles GET requests."
        try:
            logging.info("WebAPI: Received GET request.")
            self.__handle_request()
        except Exception as err:
            logging.critical("Error in WebApi: %s", err.with_traceback(None))
            self.send_response(401)
            self.end_headers()

    def __handle_request(self):
        parsed = self.__parse_path()
        if parsed is None:
            logging.error("Parsing request failed: %s", self.path)
            raise HomeBaseError.WebRequestParseError
        (kind, command, query) = parsed
        logging.info("WebAPI: %s", command)
        topic = Topic.from_str(query["topic"])
        logging.debug("WebAPI: %s to/of %s", command, topic)
        if topic.category == "bridge":
            logging.debug("Received a bridge-targetted message over Web API.")
            logging.debug(self.path)
            logging.debug(command)
            logging.debug(str(query))
        if kind == 'command':
            return self.__handle_command(command=command, topic=topic, payload=query)
        elif kind == 'query':
            return self.__handle_query(query_str=command, topic=topic)
        logging.error("Parsing request kind failed: %s", kind)
        raise HomeBaseError.WebRequestParseError

    def __parse_path(self) -> Optional[Tuple[str, str, Dict[str, str]]]:
        parsed = url.urlparse(self.path)
        split = parsed.path.split('/')
        if len(split) != 3 or split[0] != '':
            logging.error("Length of path is not 3 or the first entry is not empty.")
            raise HomeBaseError.WebRequestParseError
        kind = split[1]
        command = split[2]
        query = url.parse_qs(parsed.query)
        if "topic" not in query or len(query["topic"]) == 0:
            logging.error("Either there is no topic or the topic is empty.")
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
            logging.error("Query does not contain a valid command: %s", query)
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
            logging.error("Did not get a response within 60 seconds.")
            raise HomeBaseError.QueryNoResponse from ecx
        logging.debug("Responding to query with: %s", resp)
        self.wfile.write(str.encode(resp))
        return

    def __handle_command(self, command: str, topic: Topic, payload: Dict[str, str]):
        if Handler.request is None:
            raise HomeBaseError.Unreachable
        cmd = ApiCommand.from_str(command)
        if cmd is None:
            logging.error("Command does not contain a valid command: %s", command)
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

    def _run(self):
        "Starts serving TCP requests."
        try:
            httpd = TCPServer(("", 8088), Handler)
            httpd.serve_forever()
        except OSError as ose:
            print("Failed attempt to bind socket.")
            raise ose
