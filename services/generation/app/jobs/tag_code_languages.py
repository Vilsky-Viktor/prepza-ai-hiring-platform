"""Tags the examples of questions saved before generation gave each its language ("```" becomes
"```python"), so the site shows them in their colors. With --text it checks the ones tagged
"text" instead, which an example showing several files used to get though it's in one
notation: those the model names a notation for get it, the rest stay "text". Safe to run again:
it only picks examples still without a language, or still tagged "text".

Run from the repo root:
    docker-compose exec generation uv run --no-sync python -m app.jobs.tag_code_languages [--text]
"""

import asyncio
import logging
import sys

from langchain_core.messages import HumanMessage
from prepza_common.logging import configure_logging

from app.constants.code import TAG_BATCH_SIZE, TEXT_FENCE, UNTAGGED_FENCE
from app.helpers.code import example_of
from app.integrations import library, llm
from app.prompts.code_languages import CODE_LANGUAGES_PROMPT
from app.schemas.code import CodeTagList

logger = logging.getLogger(__name__)


async def tag_code_languages(text: bool = False) -> int:
    """Tags every untagged example, or with `text` re-tags the "text" ones; how many changed."""
    structured = llm.get_code_tags_llm().with_structured_output(CodeTagList)
    fence = TEXT_FENCE if text else UNTAGGED_FENCE
    done = 0
    after = None

    while questions := await library.untagged_code(TAG_BATCH_SIZE, text, after):
        after = questions[-1]["id"]
        examples = "\n\n".join(
            f"{index}.\n{example_of(question['text'], fence)}"
            for index, question in enumerate(questions)
        )
        result: CodeTagList = await structured.ainvoke(
            [HumanMessage(content=CODE_LANGUAGES_PROMPT.format(examples=examples))]
        )
        languages = {
            questions[item.id]["id"]: item.language
            for item in result.items
            if 0 <= item.id < len(questions)
        }

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
