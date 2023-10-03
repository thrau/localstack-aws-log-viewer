import json
import logging
import os
import sqlite3
import time
from datetime import datetime

from localstack import config
from localstack.aws.api import RequestContext
from localstack.http import Response
from localstack.utils.analytics import get_session_id
from localstack.utils.files import mkdir

from .util import ServiceDictEncoder

LOG = logging.getLogger(__name__)


class Database:
    def __init__(self):
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        self.db_path = os.path.join(
            config.dirs.cache,
            "aws-request-inspector",
            f"session_{timestamp}_{get_session_id()}.db",
        )

    def init(self):
        if not os.path.exists(self.db_path):
            mkdir(os.path.dirname(self.db_path))

        LOG.info("Creating AWS request inspector database at %s", self.db_path)
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                "CREATE TABLE requests(request_id, timestamp, service, operation, is_internal, account_id, region, request_data, request_headers)"
            )
            con.execute(
                "CREATE TABLE responses(request_id, timestamp, duration, service, operation, status, err_code, err_msg, response_data, response_headers)"
            )

    def insert_request(self, context: RequestContext):
        with self.connect() as con:
            con.executemany(
                "INSERT INTO requests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        context.request_id,
                        datetime.utcnow(),
                        context.service.service_name,
                        context.operation.name,
                        context.is_internal_call,
                        context.account_id,
                        context.region,
                        json.dumps(context.service_request, cls=ServiceDictEncoder),
                        json.dumps(
                            context.request.headers.to_wsgi_list(),
                            cls=ServiceDictEncoder,
                        ),
                    )
                ],
            )

    def insert_response(self, context: RequestContext, response: Response):
        with self.connect() as con:
            con.executemany(
                "INSERT INTO responses VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        context.request_id,
                        datetime.utcnow(),
                        context.duration,
                        context.service.service_name,
                        context.operation.name,
                        response.status_code,
                        context.service_exception.code
                        if context.service_exception
                        else None,
                        context.service_exception.message
                        if context.service_exception
                        else None,
                        json.dumps(context.service_response, cls=ServiceDictEncoder)
                        if context.service_response
                        else None,
                        json.dumps(
                            response.headers.to_wsgi_list(),
                            cls=ServiceDictEncoder,
                        ),
                    )
                ],
            )

    def connect(self):
        return sqlite3.connect(self.db_path)

    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def fetch_by_request_id(self, request_id):
        query = """
        SELECT requests.*, responses.status, responses.err_code, responses.err_msg, responses.response_data
        FROM requests
        LEFT JOIN responses ON requests.request_id = responses.request_id
        WHERE requests.request_id = ?
        """

        with self.connect() as con:
            con.row_factory = self.dict_factory
            result = con.execute(query, (request_id,))
            return result.fetchall()

    def fetchall(self) -> list:
        query = """
        SELECT requests.*, responses.status, responses.err_code, responses.err_msg, responses.response_data
        FROM requests
        LEFT JOIN responses ON requests.request_id = responses.request_id;
        """

        with self.connect() as con:
            con.row_factory = self.dict_factory
            result = con.execute(query)
            return result.fetchall()


class RequestCollector:
    database: Database

    def __init__(self, database: Database):
        self.database = database

    def on_request(self, _chain, context: RequestContext, _response):
        if not context.service or not context.operation:
            return
        try:
            context.perf_counter = time.perf_counter()
            self.database.insert_request(context)
        except Exception:
            LOG.exception(
                "Error while inserting request %s into database", context.request_id
            )

    def on_response(self, _chain, context: RequestContext, response: Response):
        if not context.service or not context.operation:
            return
        try:
            context.duration = round(
                (time.perf_counter() - context.perf_counter) * 1000, 2
            )
            self.database.insert_response(context, response)
        except Exception:
            LOG.exception(
                "Error while inserting response %s into database", context.request_id
            )
