from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from prepza_common.constants import DEFAULT_LANGUAGE, LANGUAGES

from app.prompts.checker import VERIFIER_ROLE


def bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def language_name(code: str | None) -> str:
    """The language content is written in, as prompts name it. Older runs had none: English."""
    return LANGUAGES.get(code or DEFAULT_LANGUAGE, LANGUAGES[DEFAULT_LANGUAGE])


def checker_messages(prompt: str) -> list[BaseMessage]:
    """A key check's messages (the verifier's, the blind confirmation, the self-check): the
    checker's role, then the question to check."""
    return [SystemMessage(content=VERIFIER_ROLE), HumanMessage(content=prompt)]
