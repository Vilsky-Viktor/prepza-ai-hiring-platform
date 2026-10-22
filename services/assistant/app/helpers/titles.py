import re

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from prepza_common.constants import LANGUAGES

from app.constants.titles import MAX_TITLE_LENGTH, TITLE_EVERY
from app.prompts.titles import TITLE_SYSTEM

EMAIL = re.compile(r"\S+@\S+")


def should_title(questions: int) -> bool:
    """Whether a conversation gets a (new) title now: after its first answer, and after every
    TITLE_EVERY-th question."""
    return questions == 1 or (questions > 0 and questions % TITLE_EVERY == 0)


def clean_title(text: str) -> str | None:
    """The model's title as the history shows it: one line, no quotes, no period at the end, no
    email address, at most MAX_TITLE_LENGTH characters; None when nothing is left."""
    line = EMAIL.sub("", text.strip().splitlines()[0] if text.strip() else "")
    line = line.strip().strip("\"'“”«»„").rstrip(".").strip()

    return line[:MAX_TITLE_LENGTH].strip() or None


def title_prompt(chat: list[BaseMessage], language: str) -> list[BaseMessage]:
    """What the title model reads: its instructions, then the conversation, one line a message."""
    lines = "\n".join(f"{message.type}: {message.content}" for message in chat)
    system = TITLE_SYSTEM.format(length=MAX_TITLE_LENGTH, language=LANGUAGES[language])

    return [SystemMessage(content=system), HumanMessage(content=lines)]
