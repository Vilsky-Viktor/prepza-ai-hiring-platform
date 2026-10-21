import httpx
import pytest

from app.integrations import billing
from app.routers import links
from app.services import interview_access, link_start
from app.storage import invites
from tests.unit.test_links import INTERVIEW, linked  # noqa: F401

URL = "/links/abc/start"


@pytest.fixture
def released(monkeypatch):
    """The credits given back; an invite the candidate already has keeps "stored-key"."""
    keys = []

    async def release(key):
        keys.append(key)

    monkeypatch.setattr(billing, "release_candidate", release)

    return keys


def with_stored_key(monkeypatch, linked):  # noqa: F811
    async def held(_interview_id, _email):
        return linked["status"], "stored-key" if linked["status"] else None

    monkeypatch.setattr(invites, "held", held)


def test_an_expired_invite_that_fails_to_start_gives_its_credits_back(
    client,
    linked,  # noqa: F811
    released,
    monkeypatch,
):
    """Expiry won't give them back again: it only releases invites that haven't expired."""
    linked["status"] = "expired"
    with_stored_key(monkeypatch, linked)

    async def rounds_down(invite, interview, user):
        raise httpx.ConnectError("rounds is down")

    monkeypatch.setattr(link_start, "start_sessions", rounds_down)

    with pytest.raises(httpx.HTTPError):
        client.post(URL, json={"pledged": True})

    assert linked["held"] == ["stored-key"]
    assert released == ["stored-key"]


@pytest.mark.parametrize("status, given_back", [(None, True), ("invited", False)])
def test_a_lost_answer_from_billing_gives_back_only_a_hold_made_just_now(
    client,
    linked,  # noqa: F811
    released,
    monkeypatch,
    status,
    given_back,
):
    linked["status"] = status
    with_stored_key(monkeypatch, linked)

    async def lost(company_id, key):
        linked["held"].append(key)

        raise httpx.ReadTimeout("billing took too long")

    monkeypatch.setattr(billing, "hold_candidate", lost)

    with pytest.raises(httpx.HTTPError):
        client.post(URL, json={"pledged": True})

    assert released == (linked["held"] if given_back else [])


def not_ready(monkeypatch):
    """The link's interview without its questions yet (its generation still running)."""
    interview = INTERVIEW.__class__(
        id=INTERVIEW.id,
        company_id=INTERVIEW.company_id,
        generation_id=None,
        set_id=None,
        question_seconds=60,
        link_token="abc",
    )

    async def get_by_link(token):
        return interview

    async def as_is(found):
        return found

    async def editable(user, interview_id, editor=False):
        return interview, None, None

    monkeypatch.setattr(links.interviews, "get_by_link", get_by_link)
    monkeypatch.setattr(links, "attach_set", as_is)
    monkeypatch.setattr(interview_access, "attach_set", as_is)
    monkeypatch.setattr(links, "interview_for", editable)


def test_a_link_to_an_interview_without_questions_holds_nothing(
    client,
    linked,  # noqa: F811
    monkeypatch,
):
    """Turned on too early (before that was refused), it says it's not ready yet."""
    not_ready(monkeypatch)

    assert client.post(URL, json={"pledged": True}).status_code == 409
    assert linked["held"] == []


def test_the_link_turns_on_only_once_the_interview_has_its_questions(
    client,
    linked,  # noqa: F811
    monkeypatch,
):
    not_ready(monkeypatch)
    turned = []

    async def set_link(interview_id, token):
        turned.append(token)

    monkeypatch.setattr(links.interviews, "set_link", set_link)
    on = client.put(f"/interviews/{INTERVIEW.id}/link", json={"on": True})
    off = client.put(f"/interviews/{INTERVIEW.id}/link", json={"on": False})

    assert (on.status_code, off.status_code) == (409, 200)
    assert turned == [None]
