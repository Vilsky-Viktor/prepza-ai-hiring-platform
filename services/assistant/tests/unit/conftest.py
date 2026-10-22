import httpx
import pytest
from fake_redis import FakeRedis

from app.integrations import services
from app.services import actions
from app.storage import actions as store
from tests.unit.actions_setup import COMPANY


class Writes(list):
    """The services' writes; each answers `status`. `referrals`: the referral code each carried."""

    status = 201

    def __init__(self):
        super().__init__()
        self.referrals = []


@pytest.fixture
def redis(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(store, "get_redis", lambda: fake)
    monkeypatch.setattr(actions, "get_redis", lambda: fake)

    async def nothing(*args, **kwargs):
        pass

    async def owned(conversation_id, user_id, token, language):
        return None

    async def companies(user_id, fresh=False):
        return frozenset({COMPANY})

    monkeypatch.setattr(actions, "refuse_if_paused", nothing)
    monkeypatch.setattr(actions, "hit", nothing)
    monkeypatch.setattr(actions.limits, "check", nothing)
    monkeypatch.setattr(actions, "open_conversation", owned)
    monkeypatch.setattr(actions, "user_companies", companies)

    return fake


@pytest.fixture
def writes(monkeypatch):
    """The services' writes, answering 201 with a new company."""
    made = Writes()

    async def send(
        service,
        method,
        path,
        query,
        body,
        token,
        language,
        idempotency_key=None,
        via=None,
        referral=None,
    ):
        made.append((service, method, path, body, token, idempotency_key))
        made.referrals.append(referral)
        request = httpx.Request(method, f"http://{service}{path}")

        return httpx.Response(
            made.status,
            json={"id": COMPANY, "name": body["name"], "role": "owner"},
            request=request,
        )

    monkeypatch.setattr(services, "send", send)

    return made


@pytest.fixture(autouse=True)
def users_companies(monkeypatch):
    """Companies' list of the user's companies, faked: COMPANY, unless a test says otherwise;
    nothing is kept between tests."""
    from prepza_common import memory_cache

    from app.integrations import companies

    async def company_ids(user_id):
        return [COMPANY]

    monkeypatch.setattr(companies, "company_ids", company_ids)
    monkeypatch.setattr(memory_cache, "_entries", {})
