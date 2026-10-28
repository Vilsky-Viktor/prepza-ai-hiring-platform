import json
import re

import pytest
from prepza_common.config.constants import DEFAULT_LANGUAGE, LANGUAGES, LEGAL_VERSIONS

from site_content.helpers import legal

# What a translation keeps exactly as the English has it: addresses, links, numbers and dates.
KEPT = re.compile(r"[\w.+-]+@[\w.-]+\.\w+|prepza\.ai/[\w/?=-]*|\d+(?:[.,]\d+)?")

CASES = [
    (document, language)
    for document in LEGAL_VERSIONS
    for language in sorted(LANGUAGES)
    if language != DEFAULT_LANGUAGE
]


def texts(document: dict) -> list[str]:
    found = [document["intro"]]

    for section in document["sections"]:
        found += [section["heading"], *section.get("paragraphs", []), *section.get("items", [])]

    return found


def shape(document: dict) -> list[tuple[int, int]]:
    return [
        (len(section.get("paragraphs", [])), len(section.get("items", [])))
        for section in document["sections"]
    ]


@pytest.mark.parametrize("document, language", CASES)
def test_every_current_version_is_translated_with_the_same_shape_and_facts(document, language):
    """The current version in every language: the same sections, paragraphs and items, and the
    same addresses, links, numbers and dates as the English, the binding text."""
    english = legal.current(document)
    path = legal.ARCHIVE / document / LEGAL_VERSIONS[document] / f"{language}.json"
    translated = json.loads(path.read_text())

    assert shape(translated) == shape(english)

    for source, target in zip(texts(english), texts(translated), strict=True):
        assert sorted(KEPT.findall(source)) == sorted(KEPT.findall(target)), target
