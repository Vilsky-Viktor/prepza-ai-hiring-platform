"""Finds the answers people voted down (a thumbs down on the assistant's or the help chat's
answer), for a person to turn into made-up eval cases that fail the same way, each with the
answer an expert would give as its reference (datasets/README.md, Feedback cases). From Langfuse
when it's set up (the `user_vote` scores, 0 for a thumbs down, and their traces' model calls);
otherwise from the local votes tables (the assistant's messages, the help chat's help_votes), in
the same shape (disliked_shape.py). Runs in the assistant's container, free:

    READ_LANGFUSE=1 evals/run.sh assistant disliked_answers.py

Writes results/disliked_answers.json, which is git-ignored: it holds users' text, which never
goes into a dataset. Prints only how many it found, by source."""

import asyncio
from collections import Counter

from common import RESULTS, save
from disliked_shape import disliked, exchange
from prepza_common.ai import tracing
from prepza_common.ai.answer_votes import VOTE_SCORE

from assistant.core.db import Session
from assistant.repositories import help_votes, messages

# Langfuse's value of a thumbs down (answer_votes: 1 up, 0 down).
DOWN_SCORE = 0
PAGE = 100


async def local() -> tuple[list[dict], dict[str, str]]:
    """The answers voted down here, and which chat each trace is from."""
    async with Session() as session:
        answers = await messages.voted_down(session)
        helped = await help_votes.voted_down(session)

    found = [
        disliked("assistant", m.trace_id, m.created_at.isoformat(), asked, m.content)
        for m, asked in answers
    ]
    found += [disliked("help", v.trace_id, v.updated_at.isoformat(), None, None) for v in helped]
    sources = {row["trace_id"]: row["source"] for row in found if row["trace_id"]}

    return found, sources


def from_langfuse(sources: dict[str, str]) -> list[dict]:
    """Every thumbs down in Langfuse, with its trace's question and answer."""
    client = tracing.client()
    found = []
    cursor = None

    while True:
        page = client.api.scores.get_many(
            name=VOTE_SCORE, fields="subject", limit=PAGE, cursor=cursor
        )
        found += [
            (score.subject.id, score.timestamp.isoformat())
            for score in page.data
            if score.value == DOWN_SCORE and score.subject and score.subject.kind == "trace"
        ]
        cursor = page.meta.cursor

        if not cursor:
            break

    rows = []

    for trace_id, date in found:
        calls = client.api.observations.get_many(
            trace_id=trace_id, type="GENERATION", fields="core,basic,io", limit=PAGE
        ).data
        question, answer = exchange([(c.start_time, c.input, c.output) for c in calls])
        rows.append(disliked(sources.get(trace_id, "unknown"), trace_id, date, question, answer))

    return rows


async def main() -> None:
    found, sources = await local()

    if tracing.tracing_on():
        found = from_langfuse(sources)
        where = "Langfuse"
    else:
        where = "the local votes tables"

    save(RESULTS / "disliked_answers.json", {"from": where, "answers": found})
    counts = dict(Counter(row["source"] for row in found))
    print(f"{len(found)} answers voted down in {where}: {counts or 'none'}")


if __name__ == "__main__":
    asyncio.run(main())
