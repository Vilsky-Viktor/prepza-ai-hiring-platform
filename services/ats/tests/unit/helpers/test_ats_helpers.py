import asyncio

import httpx
import pytest
from fastapi import HTTPException
from testee_common.http import http

from ats.helpers.ats import html_to_text, job_text, subdomain
from ats.integrations import workable
from ats.integrations.ats_http import checked
from ats.integrations.errors import KeyRejected


@pytest.mark.parametrize(
    ("pasted", "expected"),
    [
        ("acme", "acme"),
        (" Acme.Workable.com ", "acme"),
        ("https://acme-eu.workable.com/backend/jobs", "acme-eu"),
        ("not a subdomain", None),
        ("-acme", None),
    ],
)
def test_a_pasted_workable_address_gives_its_subdomain(pasted, expected):
    assert subdomain(pasted, ".workable.com") == expected


@pytest.mark.parametrize(
    ("pasted", "expected"),
    [
        ("acme", "acme"),
        (" Acme.Recruitee.com ", "acme"),
        ("https://acme-eu.recruitee.com/app/offers", "acme-eu"),
        ("acme.workable.com", None),
        ("not a subdomain", None),
    ],
)
def test_a_pasted_recruitee_address_gives_its_subdomain(pasted, expected):
    assert subdomain(pasted, ".recruitee.com") == expected


def test_job_html_becomes_plain_text_with_lines_and_dashes():
    html = "<p>We need an <b>accountant</b>.</p><ul><li>IFRS</li><li>VAT</li></ul><br><br><p>Remote</p>"

    assert html_to_text(html) == "We need an accountant.\n\n- IFRS\n- VAT\n\nRemote"


def test_a_job_is_its_title_and_non_empty_sections_cut_to_the_limit():
    assert job_text("Accountant", ["<p>Close</p>", "", "<p>Perks</p>"], 100) == (
        "Accountant\n\nClose\n\nPerks"
    )
    assert job_text("Accountant", ["<p>Close the books</p>"], 15) == "Accountant\n\nClo"


def answering(monkeypatch, handler):
    """Workable's API, replaced by `handler` (a request in, an httpx.Response out)."""
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(http, "get_client", lambda: client)


def test_a_refused_token_and_a_failing_workable_are_told_apart(monkeypatch):
    answering(monkeypatch, lambda request: httpx.Response(401))

    with pytest.raises(KeyRejected):
        asyncio.run(workable.check("acme", "bad"))

    answering(monkeypatch, lambda request: httpx.Response(500))

    with pytest.raises(HTTPException) as failed:
        asyncio.run(workable.check("acme", "good"))

    assert failed.value.status_code == 502


def test_published_jobs_are_read_page_by_page_with_the_token(monkeypatch):
    seen = []

    def handler(request):
        seen.append((request.url.host, request.headers["authorization"], request.url.params))

        if "since_id" not in request.url.params:
            return httpx.Response(
                200,
                json={
                    "jobs": [{"shortcode": "A1", "title": "Accountant"}],
                    "paging": {"next": "https://acme.workable.com/spi/v3/jobs?since_id=42"},
                },
            )

        return httpx.Response(200, json={"jobs": [{"shortcode": "B2", "title": "Support"}]})

    answering(monkeypatch, handler)

    assert asyncio.run(workable.jobs("acme", "token")) == [
        {"id": "A1", "name": "Accountant"},
        {"id": "B2", "name": "Support"},
    ]
    assert seen[0][0] == "acme.workable.com"
    assert seen[0][1] == "Bearer token"
    assert seen[0][2]["state"] == "published"
    assert seen[1][2]["since_id"] == "42"


def test_a_jobs_stages_and_text_come_from_workable(monkeypatch):
    def handler(request):
        if request.url.path.endswith("/stages"):
            return httpx.Response(200, json={"stages": [{"slug": "assessment", "name": "Test"}]})

        return httpx.Response(
            200, json={"title": "Accountant", "description": "<p>Close</p>", "requirements": None}
        )

    answering(monkeypatch, handler)

    assert asyncio.run(workable.stages("acme", "token", "A1")) == [
        {"id": "assessment", "name": "Test"}
    ]
    assert asyncio.run(workable.job("acme", "token", "A1")) == {
        "name": "Accountant",
        "sections": ["<p>Close</p>", "", ""],
    }


def test_a_job_deleted_in_workable_is_a_404_and_an_unknown_account_a_refused_key(monkeypatch):
    answering(monkeypatch, lambda request: httpx.Response(404))

    with pytest.raises(HTTPException) as gone:
        asyncio.run(workable.job("acme", "token", "A1"))

    assert gone.value.status_code == 404

    with pytest.raises(KeyRejected):
        asyncio.run(workable.check("nobody", "token"))


def test_an_atss_rate_limit_is_passed_on_with_its_wait():
    busy = httpx.Response(429, headers={"Retry-After": "30"})

    with pytest.raises(HTTPException) as refused:
        checked(busy, "Teamtailor didn't answer", passes_429=True)

    assert (refused.value.status_code, refused.value.headers) == (429, {"Retry-After": "30"})
