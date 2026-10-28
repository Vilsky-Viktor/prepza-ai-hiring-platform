import uuid

import pytest
from event_pushes import push

from ats.models.ats import AtsConnection, AtsJobLink
from ats.repositories import ats, ats_links
from ats.repositories import ats_candidates as candidate_rows
from ats.services import ats as integrations
from ats.services import ats_candidates, reports

INTERVIEW_ID = uuid.uuid4()
COMPANY_ID = uuid.uuid4()


def post(client, event_type, data):
    return client.post("/internal/events", json=push(event_type, data))


@pytest.fixture
def calls(monkeypatch):
    """What each event leads to, recorded."""
    seen = []

    def record(name, skip=0):
        """A fake recording its arguments, without the first `skip` (a repository's session)."""

        async def fake(*args):
            seen.append((name, *args[skip:]))

        return fake

    monkeypatch.setattr(reports, "report", record("report"))
    monkeypatch.setattr(ats_candidates, "invite_waiting", record("invite_waiting"))
    monkeypatch.setattr(ats_candidates, "topped_up", record("topped_up"))
    monkeypatch.setattr(
        candidate_rows, "delete_interview_candidates", record("delete_candidates", 1)
    )
    monkeypatch.setattr(ats_links, "delete_interview_links", record("delete_links", 1))
    monkeypatch.setattr(ats, "delete_company", record("delete_company", 1))
    monkeypatch.setattr(integrations, "unsubscribe", record("unsubscribe"))
    monkeypatch.setattr(integrations, "release", record("release"))

    async def interview_links(session, interview_id):
        return []

    async def connections(session, company_id):
        return []

    async def subscriptions(session, company_id):
        return []

    monkeypatch.setattr(ats_links, "interview_links", interview_links)
    monkeypatch.setattr(ats, "connections", connections)
    monkeypatch.setattr(ats_links, "subscriptions", subscriptions)

    return seen


def test_a_finished_candidate_is_reported(client, calls):
    data = {"candidate_invite_id": str(uuid.uuid4()), "interview_id": str(INTERVIEW_ID)}

    assert post(client, "candidate.finished", data).status_code == 204
    assert calls == [("report", data)]


def test_a_ready_interview_invites_its_waiting_candidates(client, calls):
    post(client, "interview.ready", {"interview_id": str(INTERVIEW_ID)})

    assert calls == [("invite_waiting", INTERVIEW_ID)]


def test_a_deleted_interview_or_company_deletes_its_rows(client, calls):
    post(client, "interview.deleted", {"interview_id": str(INTERVIEW_ID), "company_id": "c"})
    post(client, "company.deleted", {"company_id": str(COMPANY_ID)})

    assert calls == [
        ("delete_candidates", INTERVIEW_ID),
        ("delete_links", INTERVIEW_ID),
        ("delete_company", COMPANY_ID),
    ]


def test_what_prepza_set_up_in_the_ats_is_cancelled_before_the_rows_go(client, calls, monkeypatch):
    workable = AtsConnection(id=uuid.uuid4(), provider="workable")
    breezy = AtsConnection(id=uuid.uuid4(), provider="breezy")
    linked = AtsJobLink(id=uuid.uuid4(), subscription_id="sub-1")
    unsubscribed = AtsJobLink(id=uuid.uuid4(), subscription_id=None)

    async def interview_links(session, interview_id):
        return [(linked, workable), (unsubscribed, workable)]

    async def connections(session, company_id):
        return [workable, breezy]

    async def subscriptions(session, company_id):
        return ["sub-1", "sub-2"]

    monkeypatch.setattr(ats_links, "interview_links", interview_links)
    monkeypatch.setattr(ats, "connections", connections)
    monkeypatch.setattr(ats_links, "subscriptions", subscriptions)

    post(client, "interview.deleted", {"interview_id": str(INTERVIEW_ID), "company_id": "c"})
    post(client, "company.deleted", {"company_id": str(COMPANY_ID)})

    assert calls == [
        ("unsubscribe", workable, ["sub-1"]),
        ("delete_candidates", INTERVIEW_ID),
        ("delete_links", INTERVIEW_ID),
        ("release", workable, ["sub-1", "sub-2"]),
        ("release", breezy, ["sub-1", "sub-2"]),
        ("delete_company", COMPANY_ID),
    ]


def test_a_company_that_got_credits_invites_its_candidates_short_of_them(client, calls):
    data = {"owner_type": "company", "owner_id": str(COMPANY_ID)}

    assert post(client, "credits.added", data).status_code == 204
    assert calls == [("topped_up", COMPANY_ID)]


def test_credits_another_kind_of_owner_got_are_ignored(client, calls):
    data = {"owner_type": "user", "owner_id": "ann"}

    assert post(client, "credits.added", data).status_code == 204
    assert calls == []


def test_credits_for_a_malformed_company_are_dropped_not_retried(client, calls):
    data = {"owner_type": "company", "owner_id": "acme"}

    assert post(client, "credits.added", data).status_code == 204
    assert calls == []


def test_other_events_are_ignored(client, calls):
    assert post(client, "interview.finished", {"candidate_invite_id": "x"}).status_code == 204
    assert calls == []


def test_a_failing_handler_answers_an_error_so_pubsub_retries(client, monkeypatch):
    async def failing(data):
        raise RuntimeError("ATS down")

    monkeypatch.setattr(reports, "report", failing)

    with pytest.raises(RuntimeError):
        post(client, "candidate.finished", {"candidate_invite_id": "x"})
