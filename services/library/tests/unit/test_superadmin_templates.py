import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from prepza_common.auth import current_user
from prepza_common.user import User

from app.main import app
from app.storage import preparations, templates

TEMPLATE = SimpleNamespace(
    id=uuid.uuid4(),
    kind="template",
    slug="senior-accountant",
    title="Senior accountant",
    level="hard",
    language="en",
    topic_count=7,
    created_at=datetime(2026, 10, 5, tzinfo=UTC),
    updated_at=datetime(2026, 10, 6, tzinfo=UTC),
)


@pytest.fixture
def signed_in(monkeypatch):
    """Signs in as Ann, who is the only superadmin."""
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")

    def sign_in(email):
        app.dependency_overrides[current_user] = lambda: User(
            uid="u1",
            email=email,
            email_verified=True,
            sign_in_provider="google.com",
        )

    yield sign_in

    app.dependency_overrides.clear()


@pytest.fixture
def stored(monkeypatch):
    """Templates served without a database; returns what the list was asked for."""
    asked = []

    async def list_templates(q, level, languages, offset, limit):
        asked.append((q, level, languages))

        return [TEMPLATE]

    async def get(set_id):
        return TEMPLATE if set_id == TEMPLATE.id else SimpleNamespace(kind="interview")

    async def duplicate_ids(ids):
        return set()

    monkeypatch.setattr(templates, "list_templates", list_templates)
    monkeypatch.setattr(templates, "duplicate_ids", duplicate_ids)
    monkeypatch.setattr(preparations, "get", get)

    return asked


def test_a_superadmin_lists_the_templates(client, signed_in, stored):
    signed_in("ann@example.com")

    [row] = client.get("/superadmin/templates").json()

    assert row["title"] == "Senior accountant" and row["topic_count"] == 7


def test_anyone_else_finds_no_admin_routes(client, signed_in, stored):
    signed_in("eve@example.com")

    assert client.get("/superadmin/templates").status_code == 404


def test_a_company_test_is_not_a_template(client, signed_in, stored):
    signed_in("ann@example.com")

    assert client.delete(f"/superadmin/templates/{uuid.uuid4()}").status_code == 404


def test_the_list_is_searched_and_filtered(client, signed_in, stored):
    signed_in("ann@example.com")

    client.get(
        "/superadmin/templates",
        params={"q": " Accountant ", "level": "hard", "language": ["en", "de"]},
    )

    assert stored == [("Accountant", "hard", ["en", "de"])]


def test_an_unknown_level_is_refused(client, signed_in, stored):
    signed_in("ann@example.com")

    assert client.get("/superadmin/templates", params={"level": "expert"}).status_code == 422


def test_like_wildcards_are_matched_as_typed():
    from app.helpers.search import escape_like

    assert escape_like("100%_a\\b") == "100\\%\\_a\\\\b"


def test_a_member_reviews_a_templates_topics(client, signed_in, stored, monkeypatch):
    async def get_topics(set_id):
        return [(SimpleNamespace(id=uuid.uuid4(), title="Ledgers", subtopics=["Accruals"]), 70)]

    monkeypatch.setattr(preparations, "get_topics", get_topics)
    signed_in("eve@example.com")

    found = client.get(f"/templates/{TEMPLATE.id}").json()

    assert [(t["title"], t["subtopics"], t["question_count"]) for t in found["topics"]] == [
        ("Ledgers", ["Accruals"], 70)
    ]
    assert client.get(f"/templates/{uuid.uuid4()}").status_code == 404


def test_the_practice_pages_read_templates_without_signing_in(client, stored, monkeypatch):
    async def get_topics(set_id):
        return [(SimpleNamespace(id=uuid.uuid4(), title="Ledgers", subtopics=["Accruals"]), 70)]

    monkeypatch.setattr(preparations, "get_topics", get_topics)

    listed = client.get("/templates")
    found = client.get(f"/templates/{TEMPLATE.id}")

    assert [row["title"] for row in listed.json()] == ["Senior accountant"]
    assert client.get("/templates/filters").status_code == 200
    # Topics and counts only: a template's questions are never public.
    assert "questions" not in found.json()
    assert [topic["title"] for topic in found.json()["topics"]] == ["Ledgers"]


def test_the_quality_tab_is_for_superadmins_only(client, signed_in):
    signed_in("eve@example.com")

    assert client.get("/superadmin/quality/flagged").status_code == 404
    assert client.get("/superadmin/quality/replaced").status_code == 404


@pytest.fixture
def flagged_question(monkeypatch):
    """A question flagged "wrong_key" in a set of `kind`; returns what the actions did."""
    done = []
    state = {"kind": "template", "flag": "wrong_key"}

    async def get_for_question(_question_id):
        return SimpleNamespace(kind=state["kind"])

    async def load(_question_id):
        return SimpleNamespace(), SimpleNamespace(flag=state["flag"]), {}, 0, 0

    async def verify(question_id, flag, now=False):
        done.append(("verify", flag, now))

    async def save_flag(question_id, flag, kept=False, notice=None):
        done.append(("save", flag, kept))

    from app.integrations import generation
    from app.storage import quality

    monkeypatch.setattr(preparations, "get_for_question", get_for_question)
    monkeypatch.setattr(quality, "load", load)
    monkeypatch.setattr(quality, "save_flag", save_flag)
    monkeypatch.setattr(generation, "verify_question", verify)

    return state, done


def test_a_superadmin_fixes_now_or_dismisses_a_flagged_template_question(
    client, signed_in, flagged_question
):
    state, done = flagged_question
    signed_in("ann@example.com")
    question = uuid.uuid4()

    assert client.post(f"/superadmin/quality/{question}/fix").status_code == 202
    assert client.post(f"/superadmin/quality/{question}/dismiss").status_code == 204
    assert done == [("verify", "wrong_key", True), ("save", None, True)]

    # A company's question is only viewed here, and a question that isn't flagged has nothing to do.
    state["kind"] = "interview"
    assert client.post(f"/superadmin/quality/{question}/fix").status_code == 404
    state["kind"], state["flag"] = "template", None
    assert client.post(f"/superadmin/quality/{question}/dismiss").status_code == 409


def test_a_replaced_questions_kept_reports_are_listed_newest_first(client, signed_in, monkeypatch):
    from app.storage import quality_report

    kept = SimpleNamespace(
        reports=[
            {"reason": "unclear", "comment": "Old", "created_at": "2026-10-01T10:00:00+00:00"},
            {"reason": "wrong_answer", "comment": "New", "created_at": "2026-10-04T10:00:00+00:00"},
        ]
    )

    async def revision(_revision_id):
        return kept

    monkeypatch.setattr(quality_report, "revision", revision)
    signed_in("ann@example.com")

    reports = client.get(f"/superadmin/quality/revisions/{uuid.uuid4()}/reports").json()

    assert [report["comment"] for report in reports] == ["New", "Old"]


def test_a_template_says_whether_its_pages_are_indexed(client, stored, monkeypatch):
    async def get_topics(set_id):
        return []

    async def duplicate_ids(ids):
        return set(ids)

    monkeypatch.setattr(preparations, "get_topics", get_topics)

    [listed] = client.get("/templates").json()
    found = client.get(f"/templates/{TEMPLATE.id}").json()

    assert listed["indexable"] and found["indexable"]
    assert found["updated_at"] == "2026-10-06T00:00:00Z"

    # A later template with the same title is a near-duplicate.
    monkeypatch.setattr(templates, "duplicate_ids", duplicate_ids)

    assert not client.get("/templates").json()[0]["indexable"]
