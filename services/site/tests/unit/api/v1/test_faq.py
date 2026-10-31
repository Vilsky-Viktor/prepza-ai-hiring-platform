import re
import string

from testee_common.config.constants import LANGUAGES

from site_content.constants.faq import FAQS, with_english
from site_content.constants.faq.de import FAQ as GERMAN
from site_content.constants.help import PRICES_UNAVAILABLE
from tests.unit.api.v1.test_help import CATALOG, fake_catalog

# A link in an answer: [text](/path), to one of the site's own pages.
LINK = re.compile(r"\[([^\[\]]+)\]\((/[^/\s()][^\s()]*)\)")


def test_every_faq_asks_the_english_questions_with_the_same_placeholders():
    def shape(faq):
        return [
            (
                item["key"],
                {name for _, name, _, _ in string.Formatter().parse(item["answer"]) if name},
            )
            for item in faq
        ]

    assert set(FAQS) == set(LANGUAGES)
    assert all(shape(faq) == shape(FAQS["en"]) for faq in FAQS.values())


def test_a_question_not_translated_yet_shows_in_english(client, monkeypatch):
    monkeypatch.setattr("site_content.api.v1.help.billing.catalog", fake_catalog(CATALOG))
    # German as it would be with its "cost" answer not translated yet.
    partly = [item for item in GERMAN if item["key"] != "cost"]
    monkeypatch.setitem(FAQS, "de", with_english(partly, FAQS["en"]))

    items = {
        item["key"]: item
        for item in client.get("/help/faq", headers={"Accept-Language": "de"}).json()
    }
    english = {item["key"]: item for item in FAQS["en"]}
    translated = {item["key"]: item for item in partly}

    assert items["expire"]["question"] == translated["expire"]["question"]
    assert items["cost"]["question"] == english["cost"]["question"]
    assert "500" in items["cost"]["answer"] and "{" not in items["cost"]["answer"]


def test_faq_names_prices_from_billing(client, monkeypatch):
    """Without the visitor's country (a call from another service, a test), billing's prices
    as it gives them: US dollars."""
    asked = []
    monkeypatch.setattr("site_content.api.v1.help.billing.catalog", fake_catalog(CATALOG, asked))

    items = {item["key"]: item["answer"] for item in client.get("/help/faq").json()}

    assert asked == [None]
    # 500 credits a candidate is $5, and 5 candidates a month are $300 a year.
    assert "500 credits ($5)" in items["compare_hiring"]
    assert "$300 a year" in items["compare_hiring"]
    assert "down to $2" in items["cost"]
    assert "$0 subscription" in items["expire"]
    # 1,500 welcome credits cover 3 candidates.
    assert "1,500 free credits, enough for its first 3 candidates" in items["cost"]


def test_faq_names_prices_in_the_visitors_currency(client, monkeypatch):
    asked = []
    pounds = {**CATALOG, "currency": "GBP", "candidate_cents_min": 150, "candidate_cents_max": 400}
    monkeypatch.setattr("site_content.api.v1.help.billing.catalog", fake_catalog(pounds, asked))

    items = {
        item["key"]: item["answer"]
        for item in client.get("/help/faq", params={"country": "GB"}).json()
    }

    assert asked == ["GB"]
    assert "500 credits (£4)" in items["compare_hiring"]
    assert "£240 a year" in items["compare_hiring"]
    assert "down to £1.50" in items["cost"]


def test_faq_names_no_competitor_prices():
    # Other tools' prices change and aren't ours to quote: the comparison explains the pricing
    # models instead, in every language.
    for language, items in FAQS.items():
        answer = next(item["answer"] for item in items if item["key"] == "compare_hiring")

        assert "215" not in answer and "100" not in answer, language


def test_faq_says_automatic_top_up_saves_the_card_as_a_free_subscription():
    # Automatic top-up is a $0 Paddle subscription, so no language may say there are none.
    for language, items in FAQS.items():
        answer = next(item["answer"] for item in items if item["key"] == "expire")

        assert "Paddle" in answer, language


def test_faq_says_in_every_language_how_to_stop_emails():
    # Every language answers it in its own words, not in English.
    english = next(item for item in FAQS["en"] if item["key"] == "emails")

    assert "Settings" in english["answer"] and "Unsubscribe" in english["answer"]

    for language, items in FAQS.items():
        answer = next(item["answer"] for item in items if item["key"] == "emails")

        assert language == "en" or answer != english["answer"], language


def test_faq_isnt_served_without_prices(client, monkeypatch):
    """Billing not answering: refused, so the site keeps its last good page rather than
    caching answers with blank prices."""
    monkeypatch.setattr("site_content.api.v1.help.billing.catalog", fake_catalog(None))

    response = client.get("/help/faq")

    assert response.status_code == 503
    assert response.json()["detail"] == PRICES_UNAVAILABLE


def test_faq_groups_large_numbers_as_its_language_does(client, monkeypatch):
    monkeypatch.setattr("site_content.api.v1.help.billing.catalog", fake_catalog(CATALOG))
    german = client.get("/help/faq", headers={"Accept-Language": "de"}).json()

    assert "1.500" in next(item["answer"] for item in german if item["key"] == "cost")


def test_faq_links_lead_to_the_english_pages_in_every_language():
    """An answer's links are the site's own pages, the same ones as in English, each with its
    text; no bracket is left outside a link, so nothing shows as broken markup."""

    def paths(faq):
        return {item["key"]: LINK.findall(item["answer"]) for item in faq}

    english = {key: [path for _, path in links] for key, links in paths(FAQS["en"]).items()}

    assert any(english.values())

    for language, faq in FAQS.items():
        for key, links in paths(faq).items():
            assert [path for _, path in links] == english[key], (language, key)
            assert all(text.strip() for text, _ in links), (language, key)

        for item in faq:
            rest = LINK.sub("", item["answer"])

            assert not re.search(r"[\[\]]|\]\(", rest), (language, item["key"])


def test_the_help_chat_reads_faq_links_as_their_text_and_page(client, monkeypatch):
    from testee_common.redis import memory_cache

    from site_content.helpers.help import faq_items

    monkeypatch.setattr(memory_cache, "_entries", {})
    monkeypatch.setattr("site_content.services.help.billing.catalog", fake_catalog(CATALOG))
    cost = next(item for item in faq_items("en", CATALOG) if item["key"] == "cost")

    guide = client.get("/help/guide").text

    assert "/pricing" in [path for _, path in LINK.findall(cost["answer"])]
    assert f"Q: {cost['question']}\nA: {cost['answer']}" in guide
