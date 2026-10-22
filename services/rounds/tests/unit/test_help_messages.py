"""What the help chat's model reads (services/help.py build_messages): the latest messages that
fit, each of the visitor's tagged as data, and the reply's language chosen by code."""

import asyncio

import pytest

from app.constants.help import HELP_HISTORY_CHARACTERS, HELP_HISTORY_MESSAGES
from app.prompts.help import VISITOR_MESSAGE
from app.schemas.help import HelpMessage
from app.services.help import build_messages, reply_language


def visitor(text: str) -> str:
    """A visitor's message as the model reads it: tagged as data."""
    return VISITOR_MESSAGE.format(message=text)


def test_a_long_conversation_sends_only_its_latest_messages():
    conversation = [
        HelpMessage(role="user" if index % 2 == 0 else "assistant", content=f"message {index}")
        for index in range(30)
    ] + [HelpMessage(role="user", content="last question")]
    messages = asyncio.run(build_messages(conversation, "en", None))

    assert len(messages) == 1 + HELP_HISTORY_MESSAGES + 1
    assert messages[-1].content == visitor("last question")
    assert "pricing page lists every price" in messages[0].content


def test_long_earlier_messages_are_left_out_but_the_question_stays():
    long = "x" * (HELP_HISTORY_CHARACTERS // 2 + 1)
    conversation = [
        HelpMessage(role="user", content="first"),
        HelpMessage(role="assistant", content=long),
        HelpMessage(role="user", content="again"),
        HelpMessage(role="assistant", content=long),
        HelpMessage(role="user", content="last question"),
    ]
    messages = asyncio.run(build_messages(conversation, "en", None))

    # The latest long answer and the question before it fit; the earlier long one doesn't.
    assert [message.content for message in messages[1:]] == [
        visitor("again"),
        long,
        visitor("last question"),
    ]


@pytest.mark.parametrize(
    "question, page, language",
    [
        ("Kann ich die Tests auch auf Deutsch erstellen?", "en", "de"),
        ("How do refunds work?", "de", "en"),
        ("¿Cuánto cuesta un candidato?", "en", "es"),
        ("候補者は何回まで受験できますか？", "en", "ja"),
        ("Hi", "fr", "fr"),
        ("Python", "de", "de"),
    ],
)
def test_the_reply_language_is_the_questions_when_it_shows_one_else_the_pages(
    question, page, language
):
    assert reply_language(question, page) == language
