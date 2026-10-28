"""Two throwaway English templates for the assistant's page-context test (page_context.py), which
copies an interview from each with no generation, and their removal afterwards. Saved as
generation would, with no OpenAI; their ids go to results/assistant_templates.json.

    evals/run.sh library assistant_templates.py create
    evals/run.sh library assistant_templates.py remove
"""

import asyncio
import json
import sys
import uuid
from pathlib import Path

from assistant_fixture import TEMPLATES
from prepza_common.ai.sets import OptionIn, PreparationIn, QuestionIn, TopicIn

from library.services import sets, templates

# Not common.py's paths: library has no OpenAI packages.
IDS = Path(__file__).resolve().parents[1] / "results" / "assistant_templates.json"
# A template topic's first 30 questions go to practice (library's PRACTICE_QUESTIONS); copying
# a topic needs 10 company ones.
QUESTIONS_PER_TOPIC = 40


def question(topic: str, number: int) -> QuestionIn:
    # The right option's text starts with "Right": page_context.py's candidates pick it to
    # reach the grades they're given.
    options = [OptionIn(answer=f"Right answer {number}", correct=True)]
    options += [OptionIn(answer=f"Wrong answer {number}.{n}", correct=False) for n in (1, 2, 3)]

    return QuestionIn(text=f"{topic}: question {number}?", options=options)


def fixture(title: str, topics: tuple[str, ...]) -> PreparationIn:
    return PreparationIn(
        generation_id=uuid.uuid4(),
        owner_uid="eval",
        source_text=title,
        title=title,
        level="basic",
        requirements=list(topics),
        language="en",
        topics=[
            TopicIn(
                title=topic,
                subtopics=[f"{topic} subtopic"],
                questions=[question(topic, n) for n in range(1, QUESTIONS_PER_TOPIC + 1)],
            )
            for topic in topics
        ],
    )


async def main(command: str) -> None:
    if command == "create":
        # No multi-answer questions: the candidates pick the one option starting with "Right".
        ids = [str(await templates.save_template(fixture(*item), 0)) for item in TEMPLATES]
        IDS.parent.mkdir(parents=True, exist_ok=True)
        IDS.write_text(json.dumps(ids))
        print(f"templates added: {ids}")

        return

    for template_id in json.loads(IDS.read_text()):
        await sets.delete(uuid.UUID(template_id))

    IDS.unlink()
    print("templates removed")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
