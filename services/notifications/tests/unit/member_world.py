# The world the digest and reminders read, for their unit tests: companies, people and bell
# notifications (the `world` fixture in conftest.py fakes the services around them).
from datetime import UTC, datetime
from types import SimpleNamespace

NOW = datetime(2026, 10, 8, 7, 20, tzinfo=UTC)
COMPANY = {
    "id": "c1",
    "name": "Acme",
    "members": [{"user_id": "ann", "editor": True}, {"user_id": "vic", "editor": False}],
}
ON = {
    "candidate_finished": True,
    "invite_undelivered": True,
    "ats_not_invited": True,
    "interview_ready": True,
    "reminders": True,
}


def finished(company_id, link="/i1"):
    """A company's bell notification that a candidate finished."""
    return SimpleNamespace(
        recipient_id=company_id, kind="candidate_finished", link=link, data={"title": "Backend"}
    )


def person(user_id, **preferences):
    return {
        "user_id": user_id,
        "email": f"{user_id}@example.com",
        "language": "en",
        "preferences": {**ON, **preferences},
    }
