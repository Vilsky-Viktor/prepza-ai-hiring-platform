"""Questions with an example: a block shown under the question (a fenced ``` block), such as code,
a query or a command, or on other topics a few rows of data or figures. On a topic about a
notation a computer runs or reads, about a third of the questions have one, never fewer than
MIN_EXAMPLE_SHARE nor more than MAX_EXAMPLE_SHARE, of the whole topic and of each of a template's
pools; other topics are only held to the upper bound. Generation writes topics this way (with
prepza_common.ai.multi_answer's share of multi-answer questions), and library splits a template
topic's questions into its pools with pool_share()."""

import math

from prepza_common.ai.multi_answer import is_multi, multi_count

MIN_EXAMPLE_SHARE = 0.3
MAX_EXAMPLE_SHARE = 0.4
# A topic of which at least this share of the questions came with an example in a notation the
# site colors (its fence names a language other than "text") is about material written in a
# formal notation, so held to the lower bound too: asked for a third, such a topic brings about
# 30%. Other topics' examples, such as a table's rows, are "text", or there are almost none.
FORMAL_SHARE = 0.15
# The fence language of an example in no such notation.
PLAIN_TEXT = "text"


def rounded(value: float) -> int:
    """Rounded half up."""
    return math.floor(value + 0.5)


def has_example(text: str) -> bool:
    return "```" in text


def example_count(count: int) -> int:
    """How many of `count` questions on formal-notation material to ask for with an example."""
    return rounded(count / 3)


def example_range(count: int, formal: bool) -> tuple[int, int]:
    """The fewest and most of `count` questions with an example: MIN_EXAMPLE_SHARE to
    MAX_EXAMPLE_SHARE of them on a `formal` topic, at most MAX_EXAMPLE_SHARE on any other."""
    high = rounded(count * MAX_EXAMPLE_SHARE)
    low = min(rounded(count * MIN_EXAMPLE_SHARE), high) if formal else 0

    return low, high


def example_language(text: str) -> str | None:
    """The language the question's first fence names ("```python" gives "python"), or None."""
    start = text.find("```")

    if start == -1:
        return None

    end = text.find("\n", start)

    return text[start + 3 : end if end != -1 else len(text)].strip() or None


def is_formal(texts: list[str]) -> bool:
    """The questions' topic is about material written in a formal notation (FORMAL_SHARE)."""
    coloured = sum(1 for text in texts if example_language(text) not in (None, PLAIN_TEXT))

    return bool(texts) and coloured >= len(texts) * FORMAL_SHARE


def text_and_options(question) -> tuple[str, list]:
    """A question as a dict ({"text", "options"}) or as a model with those attributes."""
    if isinstance(question, dict):
        return question["text"], question["options"]

    return question.text, question.options


def pick(questions: list, count: int, multi: int, examples: tuple[int, int]) -> tuple[list, list]:
    """Up to `count` of the questions, in their order: at most `multi` multi-answer and
    `count - multi` single-answer, and from examples[0] to examples[1] with an example (at most
    `count - examples[0]` without one); and the rest, in their order."""
    low, high = examples
    room = {"multi": multi, "single": count - multi, "example": high, "plain": count - low}
    taken: list = []
    rest: list = []

    for question in questions:
        text, options = text_and_options(question)
        kinds = (
            "multi" if is_multi(options) else "single",
            "example" if has_example(text) else "plain",
        )

        if len(taken) < count and all(room[kind] > 0 for kind in kinds):
            for kind in kinds:
                room[kind] -= 1

            taken.append(question)
        else:
            rest.append(question)

    return taken, rest


def pool_share(questions: list, fresh: list, count: int, share: float) -> tuple[list, list]:
    """`count` of the `fresh` questions for one of a template topic's pools, and the rest of
    them: multi_count(count, share) multi-answer, and as large a share with an example as all of the
    topic's new `questions` (fresh and reused) hold. A kind the fresh ones are short of is made
    up with the other, so the pool keeps its size."""

    def with_example(group: list) -> int:
        return sum(1 for question in group if has_example(text_and_options(question)[0]))

    multis = sum(1 for question in fresh if is_multi(text_and_options(question)[1]))
    shown = rounded(with_example(questions) * count / len(questions)) if questions else 0
    multi = max(min(multi_count(count, share), multis), count - (len(fresh) - multis))
    shown = max(min(shown, with_example(fresh)), count - (len(fresh) - with_example(fresh)))
    taken, rest = pick(fresh, count, multi, (shown, shown))
    # The kinds can still fall short together (all the multi-answer ones with an example).
    short = count - len(taken)

    return taken + rest[:short], rest[short:]
