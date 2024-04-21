import json
from datetime import datetime, date
from io import IOBase
from typing import Any, Iterable

from localstack.config import HostAndPort
from localstack.http import Router
from werkzeug.routing import (
    RuleFactory,
    Map,
    Rule,
    Submount as WerkzeugSubmount,
    Subdomain as WerkzeugSubdomain,
)


class Subdomain(WerkzeugSubdomain):
    def __init__(
        self,
        subdomain: str,
        rules: RuleFactory | Iterable[RuleFactory],
        use_host_pattern: bool = True,
    ):
        super().__init__(
            subdomain, [rules] if isinstance(rules, RuleFactory) else rules
        )
        self.use_host_pattern = use_host_pattern

    def get_rules(self, map: Map) -> Iterable[Rule]:
        if not self.use_host_pattern:
            return super().get_rules(map)

        for rule in super().get_rules(map):
            rule.host = f"{self.subdomain}.<__host__>"
            yield rule


class Submount(WerkzeugSubmount):
    def __init__(self, path: str, rules: RuleFactory | Iterable[RuleFactory]) -> None:
        super().__init__(path, [rules] if isinstance(rules, RuleFactory) else rules)


class Routes(RuleFactory):
    """
    Wraps an object that uses @route decorators ase a RuleFactory that can be added to a router.
    """

    def __init__(self, obj: Any):
        self.obj = obj

    def get_rules(self, map: Map) -> Iterable[Rule]:
        # TODO: move to localstack.http and refactor router to use this instead
        router = Router()
        router.add(self.obj)
        return router.url_map._rules


class ServiceDictEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        # FIXME: write generalized way of serializing IO objects for streaming bodies (request or response)
        if isinstance(o, IOBase):
            return f"{o.__class__.__name__}()"
        if isinstance(o, bytes):
            return f"bytes({len(o)})"
        if isinstance(o, HostAndPort):
            return str(o)

        # FIXME: kinda hacky way to get around serialization errors
        try:
            super().default(o)
        except TypeError:
            return str(o)
