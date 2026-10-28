import asyncio
import base64

import httpx
import pytest
from prepza_common.events.notifications import NotificationKind, Recipient, notification

from notifications.constants.slack import ZERO_WIDTH_SPACE
from notifications.helpers.slack import message, read_state, signed_state
from notifications.integrations import slack

SECRET = "test-secret-that-is-at-least-32-bytes"


def test_a_state_names_its_company_user_and_nonce_until_it_expires():
    state = signed_state(SECRET, "c1", "u1", expires=1_000, nonce="n1")

    assert read_state(SECRET, state, now=999) == ("c1", "u1", "n1")
    assert read_state(SECRET, state, now=1_001) is None


def test_a_state_signed_with_another_secret_or_changed_is_refused():
    state = signed_state(SECRET, "c1", "u1", expires=1_000, nonce="n1")
    forged = base64.urlsafe_b64encode(
        base64.urlsafe_b64decode(state).replace(b"c1|", b"c2|")
    ).decode()

    assert read_state("another-secret-that-is-32-bytes-long", state, now=0) is None
    assert read_state(SECRET, forged, now=0) is None
    assert read_state(SECRET, "not-a-state", now=0) is None


def event(kind, **data):
    return notification(Recipient.COMPANY, "c1", kind, "/companies/c1/x", **data)


def shown(payload: dict) -> str:
    """What the message reads, with the invisible breaks in dots taken out."""
    return payload["text"].replace(ZERO_WIDTH_SPACE, "")


def button(payload: dict) -> str:
    return payload["blocks"][1]["elements"][0]["url"]


def test_a_finished_candidate_reads_with_the_grade_and_links_to_prepza():
    text = message(
        event(NotificationKind.CANDIDATE_FINISHED, email="a@b.c", title="Backend", grade=82),
        "https://prepza.ai",
    )

    assert shown(text) == "a@b.c finished “Backend”: 82%."
    assert button(text) == "https://prepza.ai/companies/c1/x"
    assert text["blocks"][0]["text"]["type"] == "plain_text"


def test_a_finished_candidate_opens_their_results():
    """The bell's notification opens the interview (it groups its candidates); Slack's, the
    candidate's results."""
    text = message(
        event(
            NotificationKind.CANDIDATE_FINISHED,
            email="a@b.c",
            title="Backend",
            candidate_link="/companies/c1/interviews/i1/candidates/v1",
        ),
        "https://prepza.ai",
    )

    assert button(text) == "https://prepza.ai/companies/c1/interviews/i1/candidates/v1"


def test_a_candidate_with_a_name_reads_with_it_escaped():
    data = {"email": "a@b.c", "title": "Backend", "candidate_name": "Ann <Lee>"}
    text = message(event(NotificationKind.CANDIDATE_FINISHED, **data), "https://prepza.ai")

    assert shown(text).startswith("Ann &lt;Lee&gt; (a@b.c) finished “Backend”.")


def test_a_not_invited_candidate_names_the_ats_and_why():
    text = message(
        event(
            NotificationKind.ATS_NOT_INVITED,
            email="a@b.c",
            title="Backend",
            ats="Greenhouse",
            reason="credits",
        ),
        "https://prepza.ai",
    )

    assert shown(text).startswith(
        "a@b.c from Greenhouse wasn't invited to “Backend”: out of credits."
    )


def test_what_people_wrote_is_shown_not_read_as_slack_markup():
    text = message(
        event(NotificationKind.INTERVIEW_READY, title="<!channel> R&D <https://x|y>"),
        "https://prepza.ai",
    )

    assert shown(text) == "The interview “&lt;!channel&gt; R&amp;D &lt;https://x|y&gt;” is ready."


def test_an_interview_without_a_title_is_named_without_quotes():
    finished = message(event(NotificationKind.CANDIDATE_FINISHED, email="a@b.c"), "https://x")
    ready = message(event(NotificationKind.INTERVIEW_READY), "https://x")

    assert shown(finished) == "a@b.c finished an interview."
    assert shown(ready) == "An interview is ready."


def test_a_name_that_looks_like_a_link_or_markup_stays_plain_text():
    data = {"email": "a@b.c", "title": "Backend", "candidate_name": "John www.evil-login.com *x*"}
    payload = message(event(NotificationKind.CANDIDATE_FINISHED, **data), "https://prepza.ai")

    # Slack formats no plain_text block, and a broken dot isn't linked anywhere.
    assert payload["blocks"][0]["text"]["type"] == "plain_text"
    assert "www.evil-login.com" not in payload["text"]
    assert f"www.{ZERO_WIDTH_SPACE}evil-login.{ZERO_WIDTH_SPACE}com" in payload["text"]
    assert shown(payload).startswith("John www.evil-login.com *x* (a@b.c)")


def test_a_kind_slack_doesnt_get_has_no_message():
    assert message(event(NotificationKind.QUESTION_FLAGGED, title="Acme"), "https://x") is None


@pytest.mark.parametrize("answer", [httpx.Response(404), httpx.Response(400, text="no_service")])
def test_a_web_hook_slack_says_is_gone(monkeypatch, answer):
    monkeypatch.setattr(slack.http, "get_client", lambda: client(answer))

    with pytest.raises(slack.WebhookGone):
        asyncio.run(slack.post("https://hooks.slack.com/x", "hi"))


@pytest.mark.parametrize("status", [429, 500, 503])
def test_slack_busy_or_down_is_retried_without_the_web_hooks_address(monkeypatch, status):
    """The address is a secret: the error, which reaches the logs, holds only the status."""
    monkeypatch.setattr(slack.http, "get_client", lambda: client(httpx.Response(status)))

    with pytest.raises(slack.SlackBusy) as busy:
        asyncio.run(slack.post("https://hooks.slack.com/services/T1/B1/secret", "hi"))

    assert str(busy.value) == str(status)
    assert busy.value.__context__ is None


def test_slack_too_slow_is_retried_without_the_web_hooks_address(monkeypatch):
    def slow(request):
        raise httpx.ConnectTimeout("timed out", request=request)

    slow_client = httpx.AsyncClient(transport=httpx.MockTransport(slow))
    monkeypatch.setattr(slack.http, "get_client", lambda: slow_client)

    with pytest.raises(slack.SlackBusy) as busy:
        asyncio.run(slack.post("https://hooks.slack.com/services/T1/B1/secret", "hi"))

    assert str(busy.value) == "ConnectTimeout"
    assert busy.value.__suppress_context__


def test_a_message_slack_turns_down_says_why(monkeypatch):
    answer = httpx.Response(400, text="invalid_payload")
    monkeypatch.setattr(slack.http, "get_client", lambda: client(answer))

    with pytest.raises(slack.SlackRefused, match="invalid_payload"):
        asyncio.run(slack.post("https://hooks.slack.com/x", "hi"))


def test_an_approved_code_becomes_the_channels_web_hook(monkeypatch):
    body = {
        "ok": True,
        "access_token": "xoxb-1",
        "team": {"name": "Acme"},
        "incoming_webhook": {"channel": "#hiring", "url": "https://hooks.slack.com/x"},
    }
    monkeypatch.setattr(slack.http, "get_client", lambda: client(httpx.Response(200, json=body)))

    assert asyncio.run(slack.exchange("code")) == {
        "team": "Acme",
        "channel": "#hiring",
        "url": "https://hooks.slack.com/x",
        "token": "xoxb-1",
    }


@pytest.mark.parametrize("url", ["https://attacker.example/x", "http://hooks.slack.com/x", None])
def test_a_web_hook_off_slacks_address_is_refused(monkeypatch, url):
    body = {"ok": True, "access_token": "xoxb-1", "incoming_webhook": {"url": url}}
    monkeypatch.setattr(slack.http, "get_client", lambda: client(httpx.Response(200, json=body)))

    with pytest.raises(slack.SlackRefused, match="invalid_webhook"):
        asyncio.run(slack.exchange("code"))


def test_a_refused_code_says_why(monkeypatch):
    answer = httpx.Response(200, json={"ok": False, "error": "invalid_code"})
    monkeypatch.setattr(slack.http, "get_client", lambda: client(answer))

    with pytest.raises(slack.SlackRefused, match="invalid_code"):
        asyncio.run(slack.exchange("code"))


def client(answer: httpx.Response) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(lambda request: answer))


def test_a_state_signed_beyond_ascii_is_refused_not_an_error():
    state = base64.urlsafe_b64encode("c1|u1|9999999999|n1|ä".encode()).decode()

    assert read_state("secret", state, 1000) is None
