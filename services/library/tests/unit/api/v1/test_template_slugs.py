import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from library.helpers.slugs import slugify, unique_slug
from library.repositories import preparations, templates

TEMPLATE = SimpleNamespace(
    id=uuid.uuid4(),
    kind="template",
    slug="senior-accountant",
    title="Senior accountant",
    level="hard",
    language="en",
    topic_count=2,
    created_at=datetime(2026, 10, 5, tzinfo=UTC),
    updated_at=datetime(2026, 10, 5, tzinfo=UTC),
)


def test_a_slug_is_lowercase_ascii_joined_by_dashes():
    assert slugify("  Senior Café Manager (C++/Go) ") == "senior-cafe-manager-c-go"
    assert slugify("Ingeniería de datos — Señor") == "ingenieria-de-datos-senor"


def test_a_long_title_is_cut_without_a_trailing_dash():
    slug = slugify("word " * 40)

    assert len(slug) <= 80 and not slug.endswith("-")


def test_a_title_without_ascii_letters_gets_a_plain_slug():
    assert slugify("Бухгалтер") == "template"


def test_a_taken_slug_gets_the_next_free_number():
    assert unique_slug("backend", set()) == "backend"
    assert unique_slug("backend", {"backend", "backend-2"}) == "backend-3"


def test_the_words_of_other_template_routes_are_never_slugs():
    assert unique_slug(slugify("Filters"), set()) == "filters-2"
    assert unique_slug("copyable", set()) == "copyable-2"


@pytest.fixture
def stored(monkeypatch):
    """One template, found by its id or slug; anything else is a company's test or missing."""
    asked = []

    async def get(set_id):
        return TEMPLATE if set_id == TEMPLATE.id else SimpleNamespace(kind="interview")

    async def get_by_slug(slug):
        return TEMPLATE if slug == TEMPLATE.slug else None

    async def get_topics(set_id):
        return [(SimpleNamespace(id=uuid.uuid4(), title="Ledgers", subtopics=[]), 5)]

    async def sample_questions(template_id, limit):
        asked.append((template_id, limit))
        question = SimpleNamespace(
            id=uuid.uuid4(), text="Debit?", options=[{"answer": "Left", "correct": True}]
        )

        return [(question, "Ledgers")]

    async def duplicate_ids(ids):
        return set()

    monkeypatch.setattr(preparations, "get", get)
    monkeypatch.setattr(preparations, "get_topics", get_topics)
    monkeypatch.setattr(templates, "get_by_slug", get_by_slug)
    monkeypatch.setattr(templates, "sample_questions", sample_questions)
    monkeypatch.setattr(templates, "duplicate_ids", duplicate_ids)

    return asked


def test_a_template_is_found_by_its_slug_or_its_id(client, stored):
    by_slug = client.get("/templates/senior-accountant").json()
    by_id = client.get(f"/templates/{TEMPLATE.id}").json()

    assert by_slug["id"] == by_id["id"] == str(TEMPLATE.id)
    assert by_slug["slug"] == "senior-accountant"
    assert by_slug["created_at"].startswith("2026-10-05")
    # Two topics: too thin for search engines.
    assert by_slug["indexable"] is False
    assert client.get("/templates/no-such-template").status_code == 404
    assert client.get(f"/templates/{uuid.uuid4()}").status_code == 404


def test_the_sample_has_questions_with_answers_and_their_topic(client, stored):
    [question] = client.get("/templates/senior-accountant/sample").json()

    assert question["topic"] == "Ledgers" and question["text"] == "Debit?"
    assert question["options"] == [{"answer": "Left", "correct": True}]
    # At most 5, the examples a role test page shows.
    assert stored == [(TEMPLATE.id, 5)]


def test_a_company_test_has_no_sample(client, stored):
    assert client.get(f"/templates/{uuid.uuid4()}/sample").status_code == 404
    assert client.get("/templates/no-such-template/sample").status_code == 404
