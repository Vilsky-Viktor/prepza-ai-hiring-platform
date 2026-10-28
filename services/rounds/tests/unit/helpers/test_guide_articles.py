import pytest
from prepza_common.ai.page_keys import PAGE_KEYS

from rounds.api.v1 import help as help_router
from rounds.constants import help as help_constants
from rounds.constants.help import NO_SUCH_GUIDE, PAGE_ARTICLES
from rounds.helpers import guide_articles

ENGLISH = """---
title: "How to hire testers"
seoTitle: "Hire Testers"
description: "A process for hiring testers."
updated: "2026-10-01"
---

# How to hire testers

Start with the **role**.
"""
GERMAN = """---
title: "Tester einstellen"
description: "Ein Prozess für Tester."
updated: "2026-10-02"
---

# Tester einstellen

Beginne mit der **Rolle**.
"""
OTHER = """---
title: "A guide to everything"
description: "All of it."
updated: "2026-10-03"
---

# A guide to everything

Text.
"""


@pytest.fixture
def articles(tmp_path, monkeypatch):
    """The test's own articles, as the site keeps them: English at guides/, German at de/."""
    (tmp_path / "guides").mkdir()
    (tmp_path / "de" / "guides").mkdir(parents=True)
    (tmp_path / "guides" / "hire-testers.md").write_text(ENGLISH)
    (tmp_path / "guides" / "everything.md").write_text(OTHER)
    (tmp_path / "de" / "guides" / "hire-testers.md").write_text(GERMAN)
    monkeypatch.setattr(guide_articles, "ARTICLES_ROOT", tmp_path)


def test_guides_are_listed_by_title_in_the_pages_language(client, articles):
    german = client.get("/help/guides", headers={"Accept-Language": "de"}).json()

    assert german == [
        {
            "slug": "everything",
            "language": "en",
            "title": "A guide to everything",
            "description": "All of it.",
            "updated": "2026-10-03",
            "path": "/guides/everything",
        },
        {
            "slug": "hire-testers",
            "language": "de",
            "title": "Tester einstellen",
            "description": "Ein Prozess für Tester.",
            "updated": "2026-10-02",
            "path": "/guides/hire-testers",
        },
    ]


def test_a_guide_is_served_with_its_text_without_its_heading(client, articles):
    english = client.get("/help/guides/hire-testers", headers={"Accept-Language": "en"}).json()
    german = client.get("/help/guides/hire-testers", headers={"Accept-Language": "de"}).json()

    assert english == {
        "slug": "hire-testers",
        "language": "en",
        "title": "How to hire testers",
        "description": "A process for hiring testers.",
        "updated": "2026-10-01",
        "path": "/guides/hire-testers",
        "body": "Start with the **role**.",
    }
    assert german["title"] == "Tester einstellen"
    assert german["body"] == "Beginne mit der **Rolle**."


def test_a_guide_not_translated_yet_is_served_in_english(client, articles):
    found = client.get("/help/guides/everything", headers={"Accept-Language": "de"}).json()

    assert (found["language"], found["title"]) == ("en", "A guide to everything")


@pytest.mark.parametrize("slug", ["missing", "Hire-Testers", "hire_testers", "..%2Fguides"])
def test_only_an_existing_guide_by_its_slug_is_served(client, articles, slug):
    response = client.get(f"/help/guides/{slug}", headers={"Accept-Language": "en"})

    assert response.status_code == 404
    assert response.json()["detail"] in (NO_SUCH_GUIDE, "Not Found")


def test_an_overlong_slug_is_refused(client, articles):
    assert client.get("/help/guides/" + "a" * 100).status_code == 422


def test_every_site_guide_is_read_from_where_the_site_keeps_it():
    """The real articles, at the path the image and the local stack share with the repo."""
    folder = help_constants.ARTICLES_ROOT / "guides"
    slugs = sorted(file.stem for file in folder.glob("*.md"))
    listed = guide_articles.guide_articles("en")

    assert slugs
    assert sorted(item["slug"] for item in listed) == slugs
    assert all(item["title"] != item["slug"] and item["description"] for item in listed)


def test_a_pages_guide_links_its_article_in_the_pages_language(client, articles, monkeypatch):
    monkeypatch.setattr(help_router, "PAGE_ARTICLES", {"billing": "hire-testers"})

    german = client.get("/help/pages/billing", headers={"Accept-Language": "de"}).json()
    other = client.get("/help/pages/pricing", headers={"Accept-Language": "de"}).json()

    assert german["article"] == {
        "slug": "hire-testers",
        "language": "de",
        "title": "Tester einstellen",
        "description": "Ein Prozess für Tester.",
        "updated": "2026-10-02",
        "path": "/guides/hire-testers",
    }
    assert other["article"] is None


def test_every_linked_article_is_a_real_guide_of_a_real_page():
    for key, slug in PAGE_ARTICLES.items():
        assert key in PAGE_KEYS
        assert guide_articles.guide_article(slug, "en") is not None, slug
