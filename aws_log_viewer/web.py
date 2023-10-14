import mimetypes
from importlib import resources

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
        if not request.path.endswith("/"):
            return Response(None, status=301, headers={"Location": request.url + "/"})
        return self.load_static_file("index.html")

    @route("/static/<path:path>")
    def static(self, request: Request, path):
        return self.load_static_file(path)

    @route("/query")
    def query(self, request: Request, *args, **kwargs):
        if request_id := request.args.get("request_id"):
            return {"records": self.database.fetch_by_request_id(request_id)}

        return {"records": self.database.fetchall()}

    @route("/stream", methods=["WEBSOCKET"])
    def live_stream(self, request, *args, **kwargs):
        return self.log_streamer.on_websocket_request(request, *args, **kwargs)

    def load_static_file(self, path: str) -> Response:
        resource = resources.files(static).joinpath(path)
        if not resource.is_file():
            return Response("Not found", 404)
        mimetype = mimetypes.guess_type(resource.name)
        mimetype = (
            mimetype[0] if mimetype and mimetype[0] else "application/octet-stream"
        )
        return Response(resource.open("rb"), mimetype=mimetype)
