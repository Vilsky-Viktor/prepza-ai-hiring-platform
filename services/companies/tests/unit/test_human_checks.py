import pytest

import app.routers.companies as company_routes
import app.routers.interview_generation as generation_routes
from app.config.settings import settings
from app.main import app
from app.services import link_start
from tests.unit.test_links import linked  # noqa: F401 (fixture)


@pytest.fixture
def checks(monkeypatch):
    """The "I'm not a robot" check, on, recording which requests were asked for it."""
    asked = []

    async def require_human(request, secret):
        asked.append(request.url.path)

    monkeypatch.setattr(settings, "turnstile_secret_key", "s3cret")

    for module in (company_routes, generation_routes, link_start):
        monkeypatch.setattr(module, "require_human", require_human)

    return asked


def test_a_new_candidate_through_a_job_ads_link_is_asked_one_coming_back_isnt(
    client,
    checks,
    linked,  # noqa: F811
):
    client.post("/links/abc/start", json={"pledged": True})
    linked["status"] = "in_process"
    client.post("/links/abc/start", json={"pledged": True})

    assert checks == ["/links/abc/start"]


@pytest.mark.parametrize(
    ("owned", "via", "asked"),
    [(0, None, True), (1, None, False), (0, "assistant", False)],
)
def test_only_a_persons_first_company_on_the_site_is_asked(
    client, checks, monkeypatch, owned, via, asked
):
    from app.service_auth import request_via
    from app.storage import companies
    from tests.unit.test_companies import sign_in

    sign_in()

    async def owned_count(user_id):
        return owned

    async def name_taken(name, user_id, email, most=None):
        return None

    monkeypatch.setattr(companies, "owned_count", owned_count)
    monkeypatch.setattr(companies, "create", name_taken)
    app.dependency_overrides[request_via] = lambda: via
    client.post("/companies", json={"name": "Acme"})
    app.dependency_overrides.pop(request_via)

    assert checks == (["/companies"] if asked else [])


@pytest.mark.parametrize(("paid", "asked"), [(False, True), (True, False)])
def test_only_a_company_that_never_paid_is_asked_before_its_questions_are_made(
    client, checks, monkeypatch, paid, asked
):
    import httpx

    from app.integrations import billing, generation
    from tests.unit import test_interview_generation as review

    review.setup(monkeypatch, "admin")
    review.sign_in("bob")

    async def fake_review(generation_id, company_id, body):
        return httpx.Response(
            200, json={"status": "queued"}, request=httpx.Request("POST", "http://generation")
        )

    async def company_paid(company_id):
        return paid

    async def record(*args, **kwargs):
        pass

    monkeypatch.setattr(generation, "review", fake_review)
    monkeypatch.setattr(billing, "company_paid", company_paid)
    monkeypatch.setattr(generation_routes.audit, "record", record)
    client.post(f"/interviews/{review.INTERVIEW_ID}/generation/review", json={"selected": [0]})
    app.dependency_overrides.clear()

    assert checks == ([f"/interviews/{review.INTERVIEW_ID}/generation/review"] if asked else [])
