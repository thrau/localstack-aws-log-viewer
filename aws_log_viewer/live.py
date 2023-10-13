import json
import logging
import time
from typing import Any

from localstack.aws.api import RequestContext
from localstack.http.websocket import (
    WebSocket,
    WebSocketRequest,
    WebSocketDisconnectedError,
)
from werkzeug import Response

from .util import ServiceDictEncoder

LOG = logging.getLogger(__name__)


class LogStreamer:
    sockets: list[WebSocket]

    def __init__(self):
        self.sockets = []

    def on_websocket_request(self, request: WebSocketRequest, *args, **kwargs):
        websocket = None
        try:
            with request.accept() as websocket:
                self.sockets.append(websocket)
                while True:
                    # this is really just to have some code here that blocks the loop
                    msg = websocket.receive()
                    LOG.info("received message from log streamer websocket: %s", msg)
        except WebSocketDisconnectedError:
            LOG.debug("Websocket disconnected: %s", websocket)
        finally:
            if websocket is not None:
                self.sockets.remove(websocket)

    def notify(self, doc: Any):
        data = json.dumps(doc, cls=ServiceDictEncoder)
        for socket in self.sockets:
            socket.send(data)

    def on_http_request(self, _chain, context: RequestContext, _response):
        if not context.service or not context.operation:
            return

        if not self.sockets:
            return

        self.notify(
            {
                "type": "request",
                "request_id": context.request_id,
                "timestamp": time.time(),
                "is_internal": context.is_internal_call,
                "service": context.service.service_name,
                "operation": context.operation.name,
                "region": context.region,
                "account_id": context.account_id,
                "request_headers": context.request.headers.to_wsgi_list(),
                "request_data": context.service_request,
            }
        )

    def on_http_response(self, _chain, context: RequestContext, response: Response):
        if not context.service or not context.operation:
            return

        if not self.sockets:
            return

        if context.service_exception:
            error = {
                "message": context.service_exception.message,
                "code": context.service_exception.code,
            }
        else:
            error = {}

        self.notify(
            {
                "type": "response",
                "request_id": context.request_id,
                "timestamp": time.time(),
                "is_internal": context.is_internal_call,
                "status": response.status_code,
                "response_headers": response.headers.to_wsgi_list(),
                "response_data": context.service_response,
                "is_error": True if error else False,
                "error": error,
            }
        )
