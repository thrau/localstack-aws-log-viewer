import logging

from localstack import config
from localstack.extensions.api import Extension, aws, http

from .database import Database, RequestCollector
from .live import LogStreamer
from .web import WebApp

LOG = logging.getLogger(__name__)


class MyExtension(Extension):
    name = "aws-request-inspector"

    def __init__(self):
        self.request_collector: RequestCollector | None = None
        self.database: Database | None = None
        self.log_streamer: LogStreamer | None = None

    def on_extension_load(self):
        logging.getLogger("aws_request_inspector").setLevel(
            level=logging.DEBUG if config.DEBUG else logging.INFO
        )
        LOG.info("Loading AWS request inspector")

        self.database = Database()
        self.request_collector = RequestCollector(self.database)
        self.log_streamer = LogStreamer()

    def on_platform_start(self):
        self.database.init()

    def update_gateway_routes(self, router: http.Router[http.RouteHandler]):
        webapp = WebApp(self.database, self.log_streamer)
        router.add(webapp)

    def update_request_handlers(self, handlers: aws.CompositeHandler):
        handlers.append(self.request_collector.on_request)
        handlers.append(self.log_streamer.on_http_request)

    def update_response_handlers(self, handlers: aws.CompositeResponseHandler):
        handlers.append(self.request_collector.on_response)
        handlers.append(self.log_streamer.on_http_response)
