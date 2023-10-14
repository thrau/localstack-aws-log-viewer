import logging

from localstack import config
from localstack.extensions.api import Extension, aws, http

from .database import Database, RequestCollector
from .live import LogStreamer
from .util import Routes, Subdomain, Submount
from .web import WebApp

LOG = logging.getLogger(__name__)


class LogViewerExtension(Extension):
    name = "aws-log-viewer"

    def __init__(self):
        self.request_collector: RequestCollector | None = None
        self.database: Database | None = None
        self.log_streamer: LogStreamer | None = None

    def on_extension_load(self):
        logging.getLogger("aws_log_viewer").setLevel(
            level=logging.DEBUG if config.DEBUG else logging.INFO
        )
        LOG.info("Loading AWS log viewer")

        self.database = Database()
        self.request_collector = RequestCollector(self.database)
        self.log_streamer = LogStreamer()

    def on_platform_start(self):
        self.database.init()

    def update_gateway_routes(self, router: http.Router[http.RouteHandler]):
        from localstack.aws.handlers.cors import ALLOWED_CORS_ORIGINS

        webapp = Routes(WebApp(self.database, self.log_streamer))

        LOG.info(
            "Serving AWS Log viewer on %s/aws-log-viewer",
            config.get_edge_url(),
        )
        LOG.info(
            "Serving AWS Log viewer on %s",
            config.get_edge_url(
                localstack_hostname=f"aws-log-viewer.{config.LOCALSTACK_HOST.host}"
            ),
        )
        ALLOWED_CORS_ORIGINS.append(f"http://aws-log-viewer.{config.LOCALSTACK_HOST}")
        ALLOWED_CORS_ORIGINS.append(f"https://aws-log-viewer.{config.LOCALSTACK_HOST}")

        router.add(Submount("/aws-log-viewer", webapp))
        router.add(Subdomain("aws-log-viewer", webapp))

    def update_request_handlers(self, handlers: aws.CompositeHandler):
        handlers.append(self.request_collector.on_request)
        handlers.append(self.log_streamer.on_http_request)

    def update_response_handlers(self, handlers: aws.CompositeResponseHandler):
        handlers.append(self.request_collector.on_response)
        handlers.append(self.log_streamer.on_http_response)
