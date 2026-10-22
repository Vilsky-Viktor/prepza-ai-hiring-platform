import asyncio
import uuid
from types import SimpleNamespace

from app.helpers.code import example_of
from app.integrations import library, llm
from app.jobs.tag_code_languages import tag_code_languages

FIRST, SECOND, THIRD = (str(uuid.uuid4()) for _ in range(3))


def test_an_example_is_read_from_its_first_untagged_block():
    assert example_of("What does it print?\n```\nprint(1)\nprint(2)\n```\nPick one.") == (
        "print(1)\nprint(2)"
    )
    assert example_of("Unclosed:\n```\nSELECT 1\n") == "SELECT 1"


def test_every_listed_example_is_tagged_and_one_the_model_skips_is_text(monkeypatch):
    pages = [
        [
            {"id": FIRST, "text": "Q?\n```\nprint(1)\n```"},
            {"id": SECOND, "text": "Q?\n```\nSELECT 1\n```"},
        ],
        [{"id": THIRD, "text": "Q?\n```\nls\n```"}],
        [],
    ]
    asked, saved = [], []

    async def untagged_code(limit, text=False, after=None):
        return pages.pop(0)

    async def save_code_languages(languages, text=False):
        saved.append(languages)

    class FakeLLM:
        def with_structured_output(self, schema):
            return self

        async def ainvoke(self, messages):
            asked.append(messages[0].content)
            # The first page's two, an out-of-range number ignored; the second page's skipped.
            items = [(0, "python"), (1, "sql"), (7, "bash")] if len(asked) == 1 else []

            return SimpleNamespace(
                items=[SimpleNamespace(id=index, language=name) for index, name in items]
            )

    monkeypatch.setattr(library, "untagged_code", untagged_code)
    monkeypatch.setattr(library, "save_code_languages", save_code_languages)
    monkeypatch.setattr(llm, "get_code_tags_llm", lambda *_: FakeLLM())

    done = asyncio.run(tag_code_languages())

    assert done == 3
    assert saved == [{FIRST: "python", SECOND: "sql"}, {THIRD: "text"}]
    assert "0.\nprint(1)" in asked[0] and "1.\nSELECT 1" in asked[0]


def test_examples_tagged_text_get_their_notation_and_genuine_plain_text_is_left_alone(
    monkeypatch,
):
    """--text: an example showing several files in one notation gets that notation; a table's
    rows stay "text", and are never listed again, so the job ends."""
    files = 'package.json\n{ "type": "module" }\nindex.js\nimport x from \'./x.js\''
    rows = "id | name\n1  | Ann"
    listed, saved, asked = [], [], []
    pages = {
        None: [
            {"id": FIRST, "text": f"Q?\n```text\n{files}\n```"},
            {"id": SECOND, "text": f"Q?\n```text\n{rows}\n```"},
        ],
        SECOND: [],
    }

    async def untagged_code(limit, text=False, after=None):
        listed.append((text, after))

        return pages[after]

    async def save_code_languages(languages, text=False):
        saved.append((languages, text))

    class FakeLLM:
        def with_structured_output(self, schema):
            return self

        async def ainvoke(self, messages):
            asked.append(messages[0].content)

            return SimpleNamespace(
                items=[
                    SimpleNamespace(id=0, language="javascript"),
                    SimpleNamespace(id=1, language="text"),
                ]
            )

    monkeypatch.setattr(library, "untagged_code", untagged_code)
    monkeypatch.setattr(library, "save_code_languages", save_code_languages)
    monkeypatch.setattr(llm, "get_code_tags_llm", lambda *_: FakeLLM())

    done = asyncio.run(tag_code_languages(text=True))

    assert done == 1
    assert saved == [({FIRST: "javascript"}, True)]
    assert listed == [(True, None), (True, SECOND)]
    assert f"0.\n{files}" in asked[0] and f"1.\n{rows}" in asked[0]
