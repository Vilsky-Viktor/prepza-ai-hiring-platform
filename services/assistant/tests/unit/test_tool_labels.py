from prepza_common.translations import TRANSLATIONS

from app.constants.chat import SESSION_EXPIRED
from app.constants.tool_labels import ACTION_LABEL, TOOL_LABELS, UNKNOWN_TOOL_LABEL
from app.constants.tools import TOOLS
from app.constants.updates import GET_UPDATES


def test_every_tool_has_a_progress_label():
    reads = {name for name, entry in TOOLS.items() if entry["method"] == "GET"}

    assert set(TOOL_LABELS) == {*reads, GET_UPDATES, "sign_out", "show"}
    assert all(label.endswith("…") for label in TOOL_LABELS.values())


def test_every_label_and_the_streamed_errors_are_translated():
    texts = {*TOOL_LABELS.values(), ACTION_LABEL, UNKNOWN_TOOL_LABEL, SESSION_EXPIRED}

    for language, messages in TRANSLATIONS.items():
        assert sorted(texts - set(messages)) == [], language
