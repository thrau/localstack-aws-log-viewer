from localstack.http import route, Request, Response

from . import static
from .database import Database
from .live import LogStreamer


class WebApp:
    database: Database
    log_streamer: LogStreamer

    def __init__(self, database: Database, log_streamer: LogStreamer):
        self.database = database
        self.log_streamer = log_streamer

    @route("/")
    def index(self, request: Request, *args, **kwargs):
        return Response.for_resource(static, "index.html")

    @route("/query")
    def query(self, request: Request, *args, **kwargs):
        if request_id := request.args.get("request_id"):
            return {"records": self.database.fetch_by_request_id(request_id)}

        return {"records": self.database.fetchall()}

    @route("/stream", methods=["WEBSOCKET"])
    def live_stream(self, request, *args, **kwargs):
        return self.log_streamer.on_websocket_request(request, *args, **kwargs)
