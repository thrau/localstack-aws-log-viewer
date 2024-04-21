import logging
import typing as t

from localstack.extensions.api import aws
from localstack.extensions.patterns.webapp import WebAppExtension
from .database import Database, RequestCollector
from .live import LogStreamer
from .web import WebApp

LOG = logging.getLogger(__name__)


class LogViewerExtension(WebAppExtension):
    name = "aws-log-viewer"

    def __init__(self):
        super().__init__(template_package_path=None)

        self.request_collector: RequestCollector | None = None
        self.database: Database | None = None
        self.log_streamer: LogStreamer | None = None

    def on_extension_load(self):
        super().on_extension_load()
        self.database = Database()
        self.request_collector = RequestCollector(self.database)
        self.log_streamer = LogStreamer()

    def on_platform_start(self):
        super().on_platform_start()
        self.database.init()

    def collect_routes(self, routes: list[t.Any]):
        routes.append(WebApp(self.database, self.log_streamer))

    def update_request_handlers(self, handlers: aws.CompositeHandler):
        super().update_request_handlers(handlers)

        handlers.append(self.request_collector.on_request)
        handlers.append(self.log_streamer.on_http_request)

    def update_response_handlers(self, handlers: aws.CompositeResponseHandler):
        super().update_response_handlers(handlers)

        handlers.append(self.request_collector.on_response)
        handlers.append(self.log_streamer.on_http_response)
