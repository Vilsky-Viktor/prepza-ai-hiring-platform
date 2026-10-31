"""Tags the examples of questions saved before generation gave each its language ("```" becomes
"```python"), so the site shows them in their colors. With --text it checks the ones tagged
"text" instead, which an example showing several files used to get though it's in one
notation: those the model names a notation for get it, the rest stay "text". Safe to run again:
it only picks examples still without a language, or still tagged "text".

Run from the repo root:
    docker-compose exec generation uv run --no-sync python -m generation.jobs.tag_code_languages [--text]
"""

import asyncio
import logging
import sys

from testee_common.observability.logging import configure_logging

from generation.constants.actions import CODE_TAGS
from generation.constants.code import TAG_BATCH_SIZE, TEXT_FENCE, UNTAGGED_FENCE
from generation.helpers.code import example_of
from generation.integrations import library
from generation.integrations.usage import ai_run
from generation.services.code_tags import tag_examples

logger = logging.getLogger(__name__)


async def tag_code_languages(text: bool = False) -> int:
    """Tags every untagged example, or with `text` re-tags the "text" ones; how many changed.
    Its model calls are one AI run (traced and priced)."""
    async with ai_run(CODE_TAGS):
        return await tag_all(text)


async def tag_all(text: bool) -> int:
    fence = TEXT_FENCE if text else UNTAGGED_FENCE
    done = 0
    after = None

    while questions := await library.untagged_code(TAG_BATCH_SIZE, text, after):
        after = questions[-1]["id"]
        found = await tag_examples([example_of(question["text"], fence) for question in questions])
        languages = {questions[index]["id"]: language for index, language in found.items()}

        if text:
            # A genuine plain-text example, or one the model skipped, stays as it is.
            languages = {key: value for key, value in languages.items() if value != "text"}
        else:
            # One the model skipped is tagged "text", so the loop always moves on.
            languages |= {
                question["id"]: "text" for question in questions if question["id"] not in languages
            }

        if languages:
            await library.save_code_languages(languages, text)

        done += len(languages)

    return done


if __name__ == "__main__":
    configure_logging()
    print(f"Tagged {asyncio.run(tag_code_languages('--text' in sys.argv))} questions")
