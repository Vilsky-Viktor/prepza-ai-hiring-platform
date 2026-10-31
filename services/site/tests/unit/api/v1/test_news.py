import asyncio
import uuid
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import jwt
import pytest
from testee_common.auth.auth import current_user
from testee_common.auth.user import User
from testee_common.config.constants import MAX_NEWS_TEXT_LENGTH, MAX_NEWS_TITLE_LENGTH
from testee_common.http.http import bearer

from site_content.helpers.notifications import news_notification
from site_content.integrations import generation
from site_content.main import app
from site_content.repositories import news, outbox
from site_content.services import news as news_service

POST_ID = uuid.uuid4()
BODY = {"title": "Practice in Thai", "text": "Line one.\nLine two.", "published_on": "2026-10-08"}


def post_row(**changes):
    values = {
        "id": POST_ID,
        "published_on": date(2026, 10, 8),
        "updated_at": datetime(2026, 10, 8, 9, 30, tzinfo=UTC),
    } | {key: value for key, value in BODY.items() if key != "published_on"}

    return SimpleNamespace(**(values | changes))


@pytest.fixture
def admin(monkeypatch):
    """Signed in as the superadmin Sam (or as `email`); storage keeps nothing, and every post
    sent to be translated is recorded with what generation gets."""
    monkeypatch.setenv("SUPERADMIN_EMAILS", "sam@testee.dev")
    sent = []
    saved = []

    async def translate_news(news_id, source):
        sent.append((news_id, source))

    async def get(session, news_id):
        return post_row()

    async def create(session, body):
        saved.append(body)

        return post_row(title=body.title, text=body.text, published_on=body.published_on)

    async def lock(session, news_id):
        return post_row()

    async def clear_translations(session, news_id):
        saved.append(("cleared", news_id))

    async def save(session, row, body):
        saved.append(body)

        return post_row(title=body.title, text=body.text, published_on=body.published_on)

    def notify(session, notice):
        saved.append(("notice", notice["kind"]))

    async def missing_languages(session, news_id):
        return ["de"]

    async def remove(session, news_id):
        saved.append(("deleted", news_id))

    monkeypatch.setattr(generation, "translate_news", translate_news)
    monkeypatch.setattr(news, "get", get)
    monkeypatch.setattr(news, "create", create)
    monkeypatch.setattr(news, "lock", lock)
    monkeypatch.setattr(news, "clear_translations", clear_translations)
    monkeypatch.setattr(news, "save", save)
    monkeypatch.setattr(outbox, "notify", notify)
    monkeypatch.setattr(news, "missing_languages", missing_languages)
    monkeypatch.setattr(news, "remove", remove)

    def sign_in(email="sam@testee.dev"):
        app.dependency_overrides[current_user] = lambda: User(
            uid="sam",
            email=email,
            email_verified=True,
            sign_in_provider="google.com",
        )

    sign_in()
    yield SimpleNamespace(sent=sent, saved=saved, sign_in=sign_in)

    app.dependency_overrides.clear()


def test_only_a_superadmin_reaches_the_news_tab(client, admin):
    admin.sign_in("ann@example.com")

    assert client.get("/superadmin/news").status_code == 404
    assert client.post("/superadmin/news", json=BODY).status_code == 404
    assert client.put(f"/superadmin/news/{POST_ID}", json=BODY).status_code == 404
    assert client.delete(f"/superadmin/news/{POST_ID}").status_code == 404
    assert admin.saved == [] and admin.sent == []


@pytest.mark.parametrize(
    "changes",
    [
        {"title": "x" * (MAX_NEWS_TITLE_LENGTH + 1)},
        {"text": "x" * (MAX_NEWS_TEXT_LENGTH + 1)},
        {"title": "   "},
        {"text": ""},
        {"published_on": None},
        {"published_on": "someday"},
    ],
)
def test_a_post_past_the_limits_or_missing_a_field_is_refused(client, admin, changes):
    response = client.post("/superadmin/news", json=BODY | changes)

    assert response.status_code == 422
    assert admin.saved == []


def test_a_new_post_at_the_limits_is_saved_trimmed_and_sent_to_be_translated(client, admin):
    body = BODY | {"title": f" {'t' * MAX_NEWS_TITLE_LENGTH} ", "text": "x" * MAX_NEWS_TEXT_LENGTH}
    response = client.post("/superadmin/news", json=body)

    assert response.status_code == 201
    assert response.json()["title"] == "t" * MAX_NEWS_TITLE_LENGTH
    assert response.json()["translated"] is False
    assert admin.saved[1:] == [("notice", "news")]
    # Generation gets the post's English and the languages it lacks, so it never calls site.
    assert admin.sent == [
        (POST_ID, {"title": BODY["title"], "text": BODY["text"], "missing": ["de"]})
    ]


def test_a_post_is_saved_even_when_generation_cant_take_it(client, admin, monkeypatch):
    async def down(news_id, source):
        raise RuntimeError("generation is down")

    monkeypatch.setattr(generation, "translate_news", down)

    assert client.post("/superadmin/news", json=BODY).status_code == 201


def test_a_new_date_alone_keeps_the_translations(client, admin):
    response = client.put(f"/superadmin/news/{POST_ID}", json=BODY | {"published_on": "2026-10-01"})

    assert response.status_code == 200
    assert response.json()["published_on"] == "2026-10-01"
    assert ("cleared", POST_ID) not in admin.saved
    assert admin.sent == []


def test_a_new_text_is_translated_again(client, admin):
    response = client.put(f"/superadmin/news/{POST_ID}", json=BODY | {"text": "Changed."})

    assert response.status_code == 200
    assert admin.saved[0] == ("cleared", POST_ID)
    assert [news_id for news_id, _ in admin.sent] == [POST_ID]


def test_editing_a_deleted_post_is_not_found(client, admin, monkeypatch):
    async def gone(session, news_id):
        return None

    monkeypatch.setattr(news, "lock", gone)

    assert client.put(f"/superadmin/news/{POST_ID}", json=BODY).status_code == 404


def test_deleting_a_post(client, admin):
    assert client.delete(f"/superadmin/news/{POST_ID}").status_code == 204
    assert admin.saved == [("deleted", POST_ID)]


def test_the_news_page_needs_no_sign_in_and_is_in_the_readers_language(client, monkeypatch):
    asked = []

    async def list_news(session, language, offset, limit):
        asked.append((language, offset, limit))

        return [(post_row(), "Übung auf Thai", "Zeile eins.")]

    monkeypatch.setattr(news, "list_news", list_news)
    response = client.get("/news?offset=20&limit=20", headers={"Accept-Language": "de-DE,de;q=0.9"})

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(POST_ID),
            "title": "Übung auf Thai",
            "text": "Zeile eins.",
            "published_on": "2026-10-08",
            "updated_at": "2026-10-08T09:30:00Z",
        }
    ]
    assert asked == [("de", 20, 20)]
    assert client.get("/news?limit=1000").status_code == 422


def service_token(lifetime=60):
    exp = datetime.now(UTC) + timedelta(seconds=lifetime)

    return jwt.encode(
        {"iss": "generation", "aud": "site", "exp": exp},
        "test-secret-that-is-at-least-32-bytes",
        algorithm="HS256",
    )


def test_a_service_reads_a_post_and_none_writes_its_translations(client, monkeypatch):
    """Notifications reads a post's English; translations arrive only as `news.translated`."""

    async def get(session, news_id):
        return post_row()

    async def missing_languages(session, news_id):
        return ["de", "fr"]

    monkeypatch.setattr(news, "get", get)
    monkeypatch.setattr(news, "missing_languages", missing_languages)
    body = {"title": "T", "text": "X", "translations": {"de": {"title": "D", "text": "Y"}}}

    headers = bearer(service_token())
    found = client.get(f"/internal/news/{POST_ID}", headers=headers)
    put = client.put(f"/internal/news/{POST_ID}/translations", json=body, headers=headers)

    assert found.json() == {"title": BODY["title"], "text": BODY["text"], "missing": ["de", "fr"]}
    assert put.status_code == 404


def test_posts_still_missing_a_translation_are_sent_again(monkeypatch):
    sent = []

    async def untranslated(session):
        return [POST_ID, gone_id]

    async def get(session, news_id):
        return post_row() if news_id == POST_ID else None

    async def missing_languages(session, news_id):
        return ["fr"]

    async def translate_news(news_id, source):
        sent.append((news_id, source["missing"]))

    gone_id = uuid.uuid4()
    monkeypatch.setattr(news, "untranslated", untranslated)
    monkeypatch.setattr(news, "get", get)
    monkeypatch.setattr(news, "missing_languages", missing_languages)
    monkeypatch.setattr(generation, "translate_news", translate_news)

    # A post deleted meanwhile isn't sent.
    assert asyncio.run(news_service.resend_untranslated()) == 2
    assert sent == [(POST_ID, ["fr"])]


def test_a_new_post_is_one_notification_for_everyone_naming_it():
    event = news_notification(post_row())

    assert event == {
        "recipient": "all",
        "recipient_id": "everyone",
        "kind": "news",
        "link": f"/news#{POST_ID}",
        "data": {"news_id": str(POST_ID), "title": BODY["title"]},
        "key": f"news:{POST_ID}",
    }


def test_the_bell_asks_for_titles_in_the_readers_language(client, monkeypatch):
    asked = []

    async def titles(session, news_ids, language):
        asked.append((news_ids, language))

        return {str(POST_ID): "Üben auf Thai"}

    monkeypatch.setattr(news, "titles", titles)
    body = {"news_ids": [str(POST_ID)], "language": "de"}

    response = client.post("/internal/news/titles", json=body, headers=bearer(service_token()))

    assert response.json() == {"titles": {str(POST_ID): "Üben auf Thai"}}
    assert asked == [([POST_ID], "de")]
