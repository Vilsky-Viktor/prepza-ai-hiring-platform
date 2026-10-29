import pytest
from prepza_common.limits import limits, rate_limit

from api.services import key_checks
from tests.unit.api.v1.test_manage_routes import public  # noqa: F401 (fixture)
from tests.unit.api_keys import call
from tests.unit.conftest import COMPANY, sign_in

KEYS = f"/manage/keys?company_id={COMPANY}"
HOOKS = f"/manage/webhooks?company_id={COMPANY}"
TOO_MANY_REQUESTS = "Too many requests. Try again later."


@pytest.fixture
def edited(monkeypatch):
    """The limits as edited in the admin zone: none unless a test puts one in."""
    values = {}

    async def current(redis):
        return values

    monkeypatch.setattr(limits, "current_values", current)

    return values


def whose(hits):
    return [(hit["limit"], hit["company_id"], hit["user_id"]) for hit in hits]


@pytest.mark.parametrize("most", [None, 3])
def test_a_company_has_at_most_the_key_limits_keys(
    client, companies_api, stored, edited, limit_hits, most
):
    if most:
        edited["MAX_API_KEYS"] = most

    most = most or 10
    sign_in()
    made = [client.post(KEYS, json={"name": "Site", "expiry": "1"}) for _ in range(most)]
    refused = client.post(KEYS, json={"name": "Site", "expiry": "1"})

    assert {response.status_code for response in made} == {201}
    assert refused.status_code == 409
    assert refused.json() == {
        "detail": f"A company can have up to {most} API keys",
        "code": "conflict",
    }
    assert len(stored["keys"]) == most
    assert whose(limit_hits) == [("MAX_API_KEYS", str(COMPANY), "u1")]


@pytest.mark.parametrize("most", [None, 2])
def test_a_company_has_at_most_the_web_hook_limits_web_hooks(
    client,
    companies_api,
    stored,
    public,  # noqa: F811
    edited,
    limit_hits,
    most,
):
    if most:
        edited["MAX_WEBHOOKS"] = most

    most = most or 5
    sign_in()
    made = [client.post(HOOKS, json={"url": f"https://example.com/{n}"}) for n in range(most)]
    refused = client.post(HOOKS, json={"url": "https://example.com/more"})

    assert {response.status_code for response in made} == {201}
    assert refused.status_code == 409
    assert refused.json() == {
        "detail": f"A company can have up to {most} web hooks",
        "code": "conflict",
    }
    assert len(stored["webhooks"]) == most
    assert whose(limit_hits) == [("MAX_WEBHOOKS", str(COMPANY), "u1")]


@pytest.mark.parametrize("most", [None, 4])
def test_a_companys_requests_a_minute_are_limited(
    client,
    companies_api,
    key,
    edited,
    limit_hits,
    monkeypatch,
    most,
):
    totals = {}

    async def counted(redis, counter, amount, window):
        totals[counter] = totals.get(counter, 0) + amount

        # The total, and 25 seconds left in the minute.
        return totals[counter], 25

    if most:
        edited["API_REQUESTS_PER_MINUTE"] = most

    most = most or 60
    monkeypatch.setattr(rate_limit, "counted", counted)
    monkeypatch.setattr(key_checks, "hit_or_skip", rate_limit.hit_or_skip)
    answered = [call(client, "GET", "/interviews").status_code for _ in range(most)]
    refused = call(client, "GET", "/interviews")

    assert set(answered) == {200}
    assert refused.status_code == 429
    assert refused.json() == {"detail": TOO_MANY_REQUESTS, "code": "rate_limited"}
    assert refused.headers["Retry-After"] == "25"
    assert totals == {f"rate:api:{COMPANY}": most + 1}
    assert whose(limit_hits) == [("API_REQUESTS_PER_MINUTE", str(COMPANY), None)]
