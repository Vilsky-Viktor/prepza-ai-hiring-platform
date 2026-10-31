"""What the help chat's model reads (services/help_chat.py build_messages): the latest messages that
fit, each of the visitor's tagged as data, and the reply's language chosen by code."""

import pytest
from testee_common.ai.scope import SCOPE_RULE
from testee_common.config.constants import OPERATOR

from assistant.constants.help_chat import HELP_HISTORY_CHARACTERS, HELP_HISTORY_MESSAGES
from assistant.prompts.help_chat import VISITOR_MESSAGE
from assistant.schemas.help_chat import HelpKnowledge, HelpMessage
from assistant.services.help_chat import build_messages, reply_language

KNOWN = HelpKnowledge(
    knowledge="<platform_guide>The pricing page lists every price.</platform_guide>"
)
ON_PRICING = HelpKnowledge(knowledge=KNOWN.knowledge, page_guide="Pricing\nWhat credits cost.")


def visitor(text: str) -> str:
    """A visitor's message as the model reads it: tagged as data."""
    return VISITOR_MESSAGE.format(message=text)


def test_a_long_conversation_sends_only_its_latest_messages():
    conversation = [
        HelpMessage(role="user" if index % 2 == 0 else "assistant", content=f"message {index}")
        for index in range(30)
    ] + [HelpMessage(role="user", content="last question")]
    messages = build_messages(conversation, "en", KNOWN)

    assert len(messages) == 1 + HELP_HISTORY_MESSAGES + 1
    assert messages[-1].content == visitor("last question")
    assert KNOWN.knowledge in messages[0].content


def test_long_earlier_messages_are_left_out_but_the_question_stays():
    long = "x" * (HELP_HISTORY_CHARACTERS // 2 + 1)
    conversation = [
        HelpMessage(role="user", content="first"),
        HelpMessage(role="assistant", content=long),
        HelpMessage(role="user", content="again"),
        HelpMessage(role="assistant", content=long),
        HelpMessage(role="user", content="last question"),
    ]
    messages = build_messages(conversation, "en", KNOWN)

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


def test_the_system_prompt_holds_the_documents_the_rules_and_the_reply_language():
    question = [HelpMessage(role="user", content="How do refunds work?")]
    system = build_messages(question, "de", KNOWN)[0].content

    assert KNOWN.knowledge in system
    assert SCOPE_RULE in system
    assert OPERATOR["email"] in system
    assert "[[sign_in]]" in system
    # The visitor wrote English on the German page: the reply is in English, chosen by code.
    assert system.rstrip().endswith("Reply in English, as a native speaker would write it.")


def test_the_page_asked_on_adds_its_guide_and_an_unknown_one_adds_nothing():
    question = [HelpMessage(role="user", content="What can I do here?")]
    on_pricing = build_messages(question, "en", ON_PRICING, "pricing")[0].content
    nowhere = build_messages(question, "en", KNOWN, "superadmin")[0].content

    assert '"pricing"' in on_pricing and ON_PRICING.page_guide in on_pricing
    assert "<page_guide>" not in nowhere and '"superadmin"' not in nowhere
