"""Topping a topic up with new questions of the kinds it lacks."""

from prepza_common.examples import has_example
from prepza_common.multi_answer import is_multi

from app.constants.generation import FILL_ATTEMPTS, FILL_SPARE_QUESTIONS
from app.helpers.questions import missing_kinds, normalize
from app.models.state import State
from app.services.dedupe import distinct_by_meaning
from app.services.nodes.questions import generate_questions


class TopicShortError(Exception):
    """A topic still lacks questions after every attempt; the generation fails and can retry."""


async def new_questions(
    item: dict, missing: int, state: State, multi: bool = False, example: bool = False
) -> list[dict]:
    """Questions with options on the topic, all of one kind: single-answer or multi-answer
    (`multi`), with an example or without (`example`); different from every one it already has,
    in words and in meaning, as the pipeline's own are."""
    count = missing + FILL_SPARE_QUESTIONS
    result = await generate_questions(
        {
            "topic_index": 0,
            "topic": item["topic"],
            "subtopic_index": 0,
            "subtopic": ", ".join(item["subtopics"]) or item["topic"],
            "count": count,
            "multi": count if multi else 0,
            "examples": count if example else 0,
            "level": state["level"],
            "existing": item["questions"],
            "language": state.get("language"),
        }
    )
    taken = {normalize(text) for text in item["questions"]}
    fresh = []

    for question in result["question_pool"][0]["questions"]:
        kind = (is_multi(question["options"]), has_example(question["text"]))

        if normalize(question["text"]) not in taken and kind == (multi, example):
            taken.add(normalize(question["text"]))
            fresh.append(question)

    existing = len(item["questions"])
    kept = await distinct_by_meaning(
        item["questions"] + [question["text"] for question in fresh], keep_first=existing
    )

    return [fresh[index - existing] for index in kept[existing:]]


async def top_up(
    item: dict,
    questions: list[dict],
    size: int,
    multi: int,
    examples: tuple[int, int],
    state: State,
) -> None:
    """Adds new questions to `questions` ({"text", "options"}) until there are `size`, `multi`
    of them multi-answer and at least examples[0] with an example (missing_kinds), each kind
    asked for apart. item ({"topic", "subtopics", "questions"}) holds every text the new ones
    must differ from, and gets theirs.

    Questions get dropped as ambiguous or by the key self-check, and a kind can fail to come
    out; the last round makes up for whatever is missing with single-answer questions without
    an example, so a topic isn't failed for its mix."""
    for attempt in range(FILL_ATTEMPTS):
        lacking = missing_kinds(size, questions, multi, examples)

        if attempt == FILL_ATTEMPTS - 1:
            lacking = {(False, False): sum(lacking.values())}

        for (kind_multi, kind_example), missing in lacking.items():
            if missing <= 0:
                continue

            # The spares asked for beyond what's missing are left out.
            fresh = await new_questions(item, missing, state, kind_multi, kind_example)

            for question in fresh[:missing]:
                questions.append(question)
                item["questions"].append(question["text"])
