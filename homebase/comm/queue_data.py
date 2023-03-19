"Data to be put into the queue."

from typing import Dict, Optional

import lighting
from comm.topic import Topic
from enums import ApiCommand, ApiQuery, QDataKind


class QData:
    "Data to be stored in the queue."
    def __init__(
        self,
        kind:     QDataKind,
        payload:  Dict[str, str],
        topic:    Optional[Topic]      = None,
        state:    Optional[lighting.State] = None,
        command:  Optional[ApiCommand] = None,
        query:    Optional[ApiQuery]   = None,
    ):
        self.kind:     QDataKind            = kind
        self.topic:    Optional[Topic]      = topic
        self.state:    Optional[lighting.State] = state
        self.command:  Optional[ApiCommand] = command
        self.query:    Optional[ApiQuery]   = query
        self.payload:  Dict[str, str]       = payload

    @staticmethod
    def refresh() -> 'QData':
        "Refresh lights based on dynamic settings"
        return QData.api_command(topic=Topic.for_home(), command=ApiCommand.Refresh, payload={})

    @staticmethod
    def api_command(topic: Topic, command: ApiCommand, payload: Dict[str, str]) -> 'QData':
        "Creates an entity of queue data for the given api command."
        return QData(
            kind=QDataKind.ApiAction,
            topic=topic,
            command=command,
            payload=payload
        )

    @staticmethod
    def api_query(topic: Topic, query: ApiQuery) -> 'QData':
        "Creates an API query."
        return QData(
            kind=QDataKind.ApiQuery,
            topic=topic,
            query=query,
            payload={}
        )
