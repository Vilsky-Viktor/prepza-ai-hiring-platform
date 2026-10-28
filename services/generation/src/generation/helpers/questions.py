import math
import random
import re

from prepza_common.ai.examples import has_example
from prepza_common.ai.multi_answer import is_multi
from prepza_common.limits.limit_list import LIMITS

from generation.constants.generation import (
    MAX_EXAMPLE_LINES,
    MAX_MULTI_CORRECT,
    MAX_OPTION_CHARS,
    MAX_QUESTION_CHARS,
    OPTIONS,
    QUESTION_BATCH_SIZE,
    QUESTION_OVERSAMPLE,
)
from generation.constants.kinds import GenerationKind
from generation.models.state import State
from generation.schemas.regenerate import QuestionContext

# A line starting with "A." or "A)" begins choices the model listed in the question itself.
LISTED_CHOICES = re.compile(r"\n\s*A[.)]\s.*", re.DOTALL)
# A Markdown fence the model put around an example itself.
EXAMPLE_FENCE = re.compile(r"^```[\w+-]*\n?|\n?```$")


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def strip_choices(question: str) -> str:
    return LISTED_CHOICES.sub("", question).strip()


def with_example(question: str, example: str | None, language: str | None = None) -> str:
    """The question as it's stored and shown: its sentences, then its example in a fenced block
    tagged with its language ("```python"), so the site can color it. A question that already
    holds a block keeps it as it is."""
    question = strip_choices(question)
    example = EXAMPLE_FENCE.sub("", (example or "").strip()).strip("\n")

    if not question or not example.strip() or "```" in question:
        return question

    return f"{question}\n```{language or ''}\n{example}\n```"


def readable(question: str, example: str | None) -> bool:
    """Short enough to read and answer within a minute (MAX_QUESTION_CHARS, MAX_EXAMPLE_LINES)."""
    lines = EXAMPLE_FENCE.sub("", (example or "").strip()).strip("\n").splitlines()

    return len(strip_choices(question)) <= MAX_QUESTION_CHARS and len(lines) <= MAX_EXAMPLE_LINES


def merge_buckets(buckets: list[list[dict]]) -> list[dict]:
    """Round-robin across buckets of {"text", "options"}, dropping exact duplicates."""
    seen = set()
    merged: list[dict] = []

    for row in range(max((len(bucket) for bucket in buckets), default=0)):
        for bucket in buckets:
            if row < len(bucket) and normalize(bucket[row]["text"]) not in seen:
                seen.add(normalize(bucket[row]["text"]))
                merged.append(bucket[row])

    return merged


def topic_size_name(template: bool) -> str:
    """The Controls value giving each topic's questions: more for a template than for a
    company's test."""
    return "TEMPLATE_QUESTIONS_PER_TOPIC" if template else "INTERVIEW_QUESTIONS_PER_TOPIC"


def topic_size(state: dict) -> int:
    """Questions each topic of the run gets, as the run started with them (run_pipeline); a run
    started before they were kept gets the default."""
    return state.get("topic_size") or LIMITS[topic_size_name(state.get("template", False))].default


def question_calls(subtopic_count: int, size: int) -> int:
    """Calls each subtopic's questions are split into; reuse lowers their size, not their number."""
    per_subtopic = math.ceil(size * QUESTION_OVERSAMPLE / subtopic_count)

    return math.ceil(per_subtopic / QUESTION_BATCH_SIZE)


def split_count(count: int, parts: int) -> list[int]:
    """`count` spread over `parts` as evenly as possible."""
    return [count // parts + (1 if part < count % parts else 0) for part in range(parts)]


def clean_options(options: list[str], taken: set[str], max_chars: int) -> list[str]:
    """Strip, dedupe (case-insensitive, also against `taken`, which they're added to), drop
    anything too long."""
    cleaned: list[str] = []

    for option in options:
        option = option.strip()
        key = normalize(option)

        if option and len(option) <= max_chars and key not in taken:
            taken.add(key)
            cleaned.append(option)

    return cleaned


def build_options(
    correct: list[str], distractors: list[str], multi: bool | None = None
) -> list[dict] | None:
    """OPTIONS options, shuffled: one correct, or for a multi-answer question 2 to
    MAX_MULTI_CORRECT, the rest wrong. None when they don't qualify, or the question isn't of the kind asked for
    (`multi`; None takes either)."""
    taken: set[str] = set()
    right = clean_options(correct, taken, MAX_OPTION_CHARS)
    wrong = clean_options(distractors, taken, MAX_OPTION_CHARS)

    if len(right) != len(correct) or len(right) > MAX_MULTI_CORRECT:
        return None

    if not right or len(right) + len(wrong) < OPTIONS:
        return None

    if multi is not None and (len(right) > 1) != multi:
        return None

    options = [{"answer": answer, "correct": True} for answer in right] + [
        {"answer": answer, "correct": False} for answer in wrong[: OPTIONS - len(right)]
    ]
    # Avoid the correct options always coming first.
    random.shuffle(options)

    return options


def count_multi(questions: list[dict]) -> int:
    """How many of the questions ({"options"}) are multi-answer."""
    return sum(1 for question in questions if is_multi(question["options"]))


def usable_questions(item: dict) -> list[dict]:
    """A topic's questions ({"text", "options"}) that kept their options; the rest were dropped."""
    return [
        {"text": text, "options": options}
        for text, options in zip(item["questions"], item["answer_options"], strict=True)
        if options
    ]


def count_examples(questions: list[dict]) -> int:
    """How many of the questions ({"text"}) have an example."""
    return sum(1 for question in questions if has_example(question["text"]))


def missing_kinds(
    size: int, questions: list[dict], multi: int, examples: tuple[int, int]
) -> dict[tuple[bool, bool], int]:
    """The questions a topic of `size` still lacks, holding `questions` ({"text", "options"}),
    by kind: (multi-answer, with an example). `multi` of the topic are multi-answer, and at
    least examples[0] have an example; the ones lacking an example are single-answer first."""
    missing = max(size - len(questions), 0)
    lack_multi = min(missing, max(multi - count_multi(questions), 0))
    lack_single = missing - lack_multi
    lack_examples = min(missing, max(examples[0] - count_examples(questions), 0))
    single_examples = min(lack_examples, lack_single)
    multi_examples = lack_examples - single_examples

    return {
        (False, True): single_examples,
        (False, False): lack_single - single_examples,
        (True, True): multi_examples,
        (True, False): lack_multi - multi_examples,
    }


def shifted(examples: tuple[int, int], held: int) -> tuple[int, int]:
    """An example range less the `held` examples a topic already has."""
    return max(examples[0] - held, 0), max(examples[1] - held, 0)


def set_company(context: QuestionContext) -> str | None:
    """The company a question's set belongs to; None for a template."""
    return context.owner_id if context.kind == GenerationKind.INTERVIEW else None


def reused_questions(state: State, topic_index: int) -> list[dict]:
    reused = state.get("reused") or []

    return reused[topic_index] if reused else []
