import json
from datetime import datetime, date
from io import BufferedReader
from typing import Any


class ServiceDictEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        # FIXME: write generalized way of serializing IO objects for streaming bodies (request or response)
        if isinstance(o, BufferedReader):
            return "BufferedReader()"
        super().default(o)
