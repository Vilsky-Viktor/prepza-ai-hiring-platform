import asyncio
import re
from pathlib import Path

from prepza_common.http import http, shutdown
from service_code import service_code

ROOT = Path(__file__).resolve().parents[5]


class Closable:
    def __init__(self, closed: list, name: str, fails: bool = False):
        self.closed, self.name, self.fails = closed, name, fails

    async def aclose(self):
        self.closed.append(self.name)

        if self.fails:
            raise ConnectionError("already gone")

    async def dispose(self):
        await self.aclose()


def test_everything_is_closed_even_when_one_fails(monkeypatch):
    closed = []
    shared = Closable(closed, "http")
    monkeypatch.setattr(http, "get_client", lambda: shared)

    asyncio.run(
        shutdown.close_shared(
            Closable(closed, "database"),
            Closable(closed, "redis", fails=True),
            Closable(closed, "webhooks"),
        )
    )

    assert closed == ["http", "webhooks", "redis", "database"]


def test_every_service_closes_what_it_holds_at_the_end_of_its_lifespan():
    """Every app's lifespan (each service's main.py, and generation's worker) ends with
    close_shared, so a stopping instance gives its database connections back at once."""
    apps = service_code(ROOT, "main.py") + service_code(ROOT, "worker_main.py", "generation")
    missing = [
        str(path.relative_to(ROOT))
        for path in apps
        if not re.search(r"yield\n(.|\n)*await close_shared\(", path.read_text())
    ]

    assert len(apps) >= 10
    assert missing == []
