import uuid
from types import SimpleNamespace

import httpx
import pytest
from prepza_common.auth import current_user
from prepza_common.translations import TRANSLATIONS
from prepza_common.user import User

from app.constants.invites import (
    TOO_MANY_INTERVIEWS_UNPAID,
    TOO_MANY_WITHOUT_CANDIDATES,
    TOO_MANY_WITHOUT_CANDIDATES_UNPAID,
)
from app.main import app
from app.routers import interviews as route
from app.services import interview_creation as creation
from app.storage import interviews
from tests.unit.fake_redis import FakeRedis

COMPANY_ID = uuid.uuid4()


@pytest.fixture(autouse=True)
def signed_in_manager(monkeypatch):
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True, name="Bob"
    )

    async def fake_company(user, company_id):
        return SimpleNamespace(id=COMPANY_ID), "owner"

    async def no_track(*args, **kwargs):
        return None

    monkeypatch.setattr(route, "require_editor", fake_company)
    monkeypatch.setattr(creation, "track", no_track)
    yield
    app.dependency_overrides.clear()


def generate(client, monkeypatch, waiting, paid=False, redis=None, refusal=None):
    """Asks for a new interview while `waiting` generated interviews have no candidate, for a
    company that topped up (`paid`) or not, with the limits and counters in `redis`; generation
    answers `refusal` (a response) when given. Returns the response and whether generation was
    reached (False, or whether it was sent as paid)."""
    reached = []
    redis = redis or FakeRedis()

    async def fake_waiting(company_id):
        return waiting

    async def fake_generation(*args):
        reached.append(args[-1])

        if refusal is not None:
            refusal.raise_for_status()

        return {"id": str(uuid.uuid4()), "language": "en"}

    async def fake_paid(company_id):
        return paid

    async def fake_create(company_id, generation_id, language, seconds):
        return SimpleNamespace(id=uuid.uuid4())

    async def fake_out(interview):
        return {
            "id": str(interview.id),
            "generation_id": str(uuid.uuid4()),
            "set_id": None,
            "generation_failed": False,
            "title": None,
            "question_seconds": 60,
            "candidate_count": 0,
            "hired": False,
            "pass_mark": 70,
            "link_token": None,
            "status": "new",
            "created_at": "2026-10-04T09:00:00Z",
        }

    async def nothing(*args, **kwargs):
        return None

    monkeypatch.setattr(interviews, "without_candidates", fake_waiting)
    monkeypatch.setattr(creation, "get_redis", lambda: redis)
    monkeypatch.setattr(creation.generation_api, "create", fake_generation)
    monkeypatch.setattr(creation.billing, "company_paid", fake_paid)
    monkeypatch.setattr(interviews, "create", fake_create)
    monkeypatch.setattr(creation, "interview_out", fake_out)
    monkeypatch.setattr(creation.audit, "record_interview", nothing)
    response = client.post(
        f"/interviews?company_id={COMPANY_ID}", json={"text": "Senior accountant job description"}
    )

    return response, reached


def generated_today(client, monkeypatch, paid, limits=None):
    """Generates until refused; the statuses and the refusal's detail."""
    redis = FakeRedis(limits)
    statuses = []

    while not statuses or statuses[-1] == 201:
        response, _ = generate(client, monkeypatch, waiting=0, paid=paid, redis=redis)
        statuses.append(response.status_code)

    return statuses, response.json()["detail"]


WAITING_UNPAID = (
    "Invite a candidate to one of your interviews, or delete one, before generating another: "
    "until your first top-up, your company's limit of generated interviews waiting without "
    "candidates is {}."
)
WAITING_PAID = (
    "Invite a candidate to one of your interviews, or delete one, before generating another: "
    "your company's limit of generated interviews waiting without candidates is {}."
)
DAY_UNPAID = (
    "Until your first top-up, your company's daily limit of generated interviews is {}. "
    "Try again tomorrow."
)
DAY_PAID = "Your company's daily limit of generated interviews is {}. Try again tomorrow."


def test_an_unpaid_company_generates_another_only_once_its_one_waiting_has_a_candidate(
    client, monkeypatch, limit_hits
):
    redis = FakeRedis()
    allowed, _ = generate(client, monkeypatch, waiting=0, redis=redis)
    response, reached = generate(client, monkeypatch, waiting=1, redis=redis)

    assert allowed.status_code == 201
    assert response.status_code == 429
    assert response.json()["detail"] == WAITING_UNPAID.format(1)
    # Refused before the day's limit, so the attempt doesn't use one of the day's.
    assert reached == []
    assert redis.counts == {f"rate:interviews:{COMPANY_ID}": 1}
    assert limit_hits == [
        {
            "limit": "MAX_INTERVIEWS_WITHOUT_CANDIDATES_UNPAID",
            "kind": "ours",
            "scope": "company",
            "company_id": str(COMPANY_ID),
            "user_id": "bob",
            "what": None,
        }
    ]


def test_a_paid_company_can_have_five_waiting(client, monkeypatch):
    allowed, _ = generate(client, monkeypatch, waiting=4, paid=True)
    refused, _ = generate(client, monkeypatch, waiting=5, paid=True)

    assert allowed.status_code == 201
    assert refused.status_code == 429
    assert refused.json()["detail"] == WAITING_PAID.format(5)


@pytest.mark.parametrize(("paid", "message"), [(False, WAITING_UNPAID), (True, WAITING_PAID)])
def test_the_waiting_limits_are_as_edited(client, monkeypatch, paid, message):
    edited = {
        "MAX_INTERVIEWS_WITHOUT_CANDIDATES": 7,
        "MAX_INTERVIEWS_WITHOUT_CANDIDATES_UNPAID": 2,
    }
    most = 7 if paid else 2
    allowed, _ = generate(client, monkeypatch, most - 1, paid, FakeRedis(edited))
    refused, _ = generate(client, monkeypatch, most, paid, FakeRedis(edited))

    assert allowed.status_code == 201
    assert refused.status_code == 429
    assert refused.json()["detail"] == message.format(most)


def test_the_days_limit_is_three_until_the_first_top_up_and_ten_after(client, monkeypatch):
    unpaid, unpaid_refusal = generated_today(client, monkeypatch, paid=False)
    paid, paid_refusal = generated_today(client, monkeypatch, paid=True)
    # An unpaid company's generation is sent as such, so the daily limit for everyone applies.
    _, reached = generate(client, monkeypatch, waiting=0)

    assert unpaid == [201] * 3 + [429]
    assert unpaid_refusal == DAY_UNPAID.format(3)
    assert paid == [201] * 10 + [429]
    assert paid_refusal == DAY_PAID.format(10)
    assert reached == [False]


def test_the_days_limits_are_as_edited(client, monkeypatch, limit_hits):
    edited = {"INTERVIEWS_PER_DAY": 4, "INTERVIEWS_PER_DAY_UNPAID": 2}
    unpaid, unpaid_refusal = generated_today(client, monkeypatch, False, edited)
    paid, paid_refusal = generated_today(client, monkeypatch, True, edited)

    assert unpaid == [201] * 2 + [429]
    assert unpaid_refusal == DAY_UNPAID.format(2)
    assert paid == [201] * 4 + [429]
    assert paid_refusal == DAY_PAID.format(4)
    assert [hit["limit"] for hit in limit_hits] == [
        "INTERVIEWS_PER_DAY_UNPAID",
        "INTERVIEWS_PER_DAY",
    ]
    assert {(hit["company_id"], hit["user_id"]) for hit in limit_hits} == {(str(COMPANY_ID), "bob")}


def test_the_limit_messages_have_translations():
    for language in TRANSLATIONS.values():
        for message in (
            TOO_MANY_WITHOUT_CANDIDATES,
            TOO_MANY_WITHOUT_CANDIDATES_UNPAID,
            TOO_MANY_INTERVIEWS_UNPAID,
        ):
            assert message in language


def generation_answer(status: int, detail: str, headers: dict | None = None) -> httpx.Response:
    request = httpx.Request("POST", "http://generation/internal/generations")

    return httpx.Response(status, json={"detail": detail}, headers=headers, request=request)


@pytest.mark.parametrize(
    ("status", "detail", "retry_after"),
    [
        (429, "Too many requests. Try again later.", "3000"),
        (503, "AI features are paused for today. They're back tomorrow.", "7200"),
    ],
)
def test_generations_refusal_reaches_the_user_and_gives_back_the_days_place(
    client, monkeypatch, status, detail, retry_after
):
    redis = FakeRedis({"INTERVIEWS_PER_DAY_UNPAID": 1})
    refusal = generation_answer(status, detail, {"Retry-After": retry_after})
    refused, _ = generate(client, monkeypatch, 0, redis=redis, refusal=refusal)
    allowed, _ = generate(client, monkeypatch, 0, redis=redis)

    assert refused.status_code == status
    assert refused.json()["detail"] == detail
    assert refused.headers["Retry-After"] == retry_after
    # The refused attempt left the day's one interview for the next.
    assert allowed.status_code == 201
    assert redis.counts == {f"rate:interviews:{COMPANY_ID}": 1}


def test_a_failed_generation_gives_back_the_days_place(client, monkeypatch):
    redis = FakeRedis()
    failure = generation_answer(500, "Internal Server Error")

    with pytest.raises(httpx.HTTPStatusError):
        generate(client, monkeypatch, 0, redis=redis, refusal=failure)

    assert redis.counts == {f"rate:interviews:{COMPANY_ID}": 0}
