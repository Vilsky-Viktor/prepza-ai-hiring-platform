import asyncio

import pytest
from prepza_common.ai.page_keys import PAGE_KEYS
from prepza_common.config.constants import LANGUAGES

from rounds.constants.help import NO_SUCH_PAGE
from rounds.helpers import page_guides
from rounds.helpers.page_guides import GUIDES
from rounds.schemas.help import HelpMessage
from rounds.services.help import build_messages
from tests.unit.api.v1.test_help import CATALOG


def test_every_page_has_its_guide_in_english():
    assert list(GUIDES["en"]) == list(PAGE_KEYS)


@pytest.mark.parametrize("language", sorted(LANGUAGES))
def test_every_page_has_a_whole_guide_in_every_language(language):
    for key in PAGE_KEYS:
        guide, english = GUIDES[language][key], GUIDES["en"][key]

        assert guide["title"] and guide["text"], (language, key)
        assert len(guide["actions"]) == len(english["actions"]), (language, key)
        assert len(guide["tips"]) == len(english["tips"]), (language, key)
        assert all(guide["actions"] + guide["tips"]), (language, key)

    assert set(GUIDES[language]) == set(PAGE_KEYS)


def test_a_guide_is_served_in_the_pages_language(client):
    german = client.get("/help/pages/billing", headers={"Accept-Language": "de"}).json()
    english = client.get("/help/pages/billing", headers={"Accept-Language": "en"}).json()

    assert german == {"key": "billing", **GUIDES["de"]["billing"], "article": None}
    assert english == {"key": "billing", **GUIDES["en"]["billing"], "article": None}


def test_a_guide_not_translated_yet_is_served_in_english(client, monkeypatch):
    untranslated = {key: guide for key, guide in GUIDES["de"].items() if key != "billing"}
    monkeypatch.setitem(page_guides.GUIDES, "de", untranslated)

    found = client.get("/help/pages/billing", headers={"Accept-Language": "de"}).json()

    assert found == {"key": "billing", **GUIDES["en"]["billing"], "article": None}


def test_an_unknown_page_has_no_guide(client):
    response = client.get("/help/pages/superadmin", headers={"Accept-Language": "en"})

    assert response.status_code == 404
    assert response.json()["detail"] == NO_SUCH_PAGE
    assert client.get("/help/pages/" + "x" * 100).status_code == 422


def test_the_help_chat_reads_the_guide_of_the_page_it_is_asked_on(redis):
    question = [HelpMessage(role="user", content="What can I do here?")]
    on_pricing = asyncio.run(build_messages(question, "de", CATALOG, "pricing"))[0].content
    nowhere = asyncio.run(build_messages(question, "de", CATALOG, "superadmin"))[0].content
    guide = GUIDES["en"]["pricing"]

    assert guide["text"] in on_pricing
    assert all(item in on_pricing for item in guide["actions"] + guide["tips"])
    assert guide["text"] not in nowhere
