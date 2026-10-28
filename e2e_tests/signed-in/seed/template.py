"""A small English template for the signed-in tests where the database has none (CI): they make
interviews from templates, since generating one needs OpenAI. Runs inside the library container,
saving it as generation would, with no OpenAI and no embedding:

    docker compose exec -T library uv run --no-sync python - < e2e_tests/signed-in/seed/template.py

A fixed generation id makes a second run find the first one's template instead of adding another.
"""

import asyncio
import uuid

from prepza_common.ai.sets import OptionIn, PreparationIn, QuestionIn, TopicIn

from library.repositories import preparations, templates

GENERATION_ID = uuid.UUID("00000000-0000-4000-8000-0000000e2e01")
TOPICS = ("SQL basics", "Indexes")
# A third of a new template's questions go to practice; copying a topic needs 10 private ones
# (MIN_COPY_QUESTIONS), so 30 leave 20, enough for every spec and its retry.
QUESTIONS_PER_TOPIC = 30


def question(topic: str, number: int) -> QuestionIn:
    options = [OptionIn(answer=f"Right answer {number}", correct=True)]
    options += [OptionIn(answer=f"Wrong answer {number}.{n}", correct=False) for n in (1, 2, 3)]

    return QuestionIn(text=f"E2E {topic}: question {number}?", options=options)


def fixture() -> PreparationIn:
    return PreparationIn(
        generation_id=GENERATION_ID,
        owner_uid="e2e-seed",
        source_text="Backend developer: SQL basics and indexes.",
        title="E2E Backend developer",
        level="basic",
        requirements=["SQL"],
        language="en",
        topics=[
            TopicIn(
                title=topic,
                subtopics=[f"{topic} subtopic"],
                questions=[question(topic, n) for n in range(1, QUESTIONS_PER_TOPIC + 1)],
            )
            for topic in TOPICS
        ],
    )


async def main() -> None:
    existing = await preparations.find_by_generation(GENERATION_ID)

    if existing:
        print(f"E2E template already there: {existing}")

        return

    print(f"E2E template added: {await templates.create_template(fixture())}")


asyncio.run(main())
