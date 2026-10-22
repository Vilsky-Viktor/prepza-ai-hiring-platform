"""A full page of a list says where the next one is (`Link: <...>; rel="next"`)."""

# The key fixture is imported from test_public_routes and named in the tests.
# ruff: noqa: F811
from urllib.parse import parse_qs, urlsplit

from app.config.settings import settings
from app.integrations import companies
from tests.unit.conftest import CANDIDATE, INTERVIEW, candidate
from tests.unit.test_public_routes import call, key  # noqa: F401 (fixture)


def next_page(response) -> tuple[str, dict] | None:
    """The next page's path and query, from the Link header."""
    link = response.headers.get("Link")

    if link is None:
        return None

    url, rel = link.split(";")
    assert rel.strip() == 'rel="next"'
    parts = urlsplit(url.strip("<>"))
    assert f"{parts.scheme}://{parts.netloc}" == settings.site_url

    return parts.path, {name: value[0] for name, value in parse_qs(parts.query).items()}


def test_a_full_page_links_the_next_by_offset_and_the_last_page_doesnt(client, companies_api, key):
    full = call(client, "GET", "/interviews", params={"offset": 2, "limit": 1})
    last = call(client, "GET", "/interviews", params={"limit": 5})

    assert next_page(full) == ("/api/v1/interviews", {"offset": "3", "limit": "1"})
    assert next_page(last) is None


def test_a_sync_links_the_next_from_the_last_items_change_and_id(
    client, companies_api, key, monkeypatch
):
    changed = "2026-10-05T08:00:00+00:00"

    async def candidates(company_id, interview_id, offset, limit, since=None, after=None):
        return [candidate(updated_at=changed)]

    monkeypatch.setattr(companies, "candidates", candidates)
    path = f"/interviews/{INTERVIEW}/candidates"
    response = call(
        client, "GET", path, params={"limit": 1, "updated_since": "2026-10-01T00:00:00Z"}
    )

    assert next_page(response) == (
        f"/api/v1{path}",
        {"limit": "1", "updated_since": changed, "after": str(CANDIDATE)},
    )
