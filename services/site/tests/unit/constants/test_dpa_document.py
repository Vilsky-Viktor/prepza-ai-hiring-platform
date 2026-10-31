from pathlib import Path

from testee_common.config.constants import LEGAL_VERSIONS

from site_content.constants.dpa import DPA_INTRO, DPA_SECTIONS

# The downloadable copy (the /documents page builds its PDF from it), kept in step with /dpa.
DOCUMENT = Path(__file__).parents[5] / "frontend/content/documents/data-processing-agreement.md"


def test_the_downloadable_dpa_says_everything_the_website_does():
    text = DOCUMENT.read_text()
    sentences = [DPA_INTRO]

    for section in DPA_SECTIONS:
        sentences += [section["heading"], *section.get("paragraphs", []), *section.get("items", [])]

    assert [sentence for sentence in sentences if sentence not in text] == []
    assert f"Version: {LEGAL_VERSIONS['dpa']}" in text
