from app.constants.untrusted_text import (
    ACTS,
    ADDRESSED,
    BRACKETED,
    COMMENT,
    HIDDEN_BLOCK,
    HIDDEN_ELEMENT,
    INSTRUCTIONS,
    INVISIBLE,
    SENTENCE_END,
    TAG,
)


def visible(text: str) -> str:
    """The text as a reader sees it: without HTML comments, scripts, elements styled or marked
    hidden and invisible characters; other tags go, their words stay."""
    for pattern in (COMMENT, HIDDEN_BLOCK, HIDDEN_ELEMENT, TAG, INVISIBLE):
        text = pattern.sub("", text)

    return text


def instruction_like(part: str) -> bool:
    """A sentence or an aside addressed to an AI and telling it to act, or written as an
    instruction to one."""
    if ADDRESSED.search(part) and ACTS.search(part):
        return True

    return any(pattern.search(part) for pattern in INSTRUCTIONS)


def without_instructions(text: str) -> str:
    """The user's visible words, without what data (an ATS job, a pasted description) may carry
    to steer the assistant: hidden content, and the sentences and bracketed asides addressed to
    an AI."""
    text = visible(text)
    text = BRACKETED.sub(
        lambda found: "" if instruction_like(found.group().strip()[1:]) else found.group(), text
    )

    return "".join(part for part in SENTENCE_END.split(text) if not instruction_like(part)).strip()
