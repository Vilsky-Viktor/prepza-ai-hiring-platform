import logging

from fastapi import HTTPException, status
from langchain_core.messages import HumanMessage, SystemMessage

from app.constants.screen import NOTHING_TO_TEST
from app.integrations import llm
from app.integrations.usage import ai_run
from app.prompts.screen import SCREEN_INPUT, SCREEN_SYSTEM
from app.schemas.screen import ScreenedText

logger = logging.getLogger(__name__)


async def names_something_testable(text: str) -> bool:
    """Whether the text names anything a test could cover (a posting, a role, skills, a goal).
    When in doubt, and when the check fails or runs out of time, the text goes through: a
    refused real role costs the user more than a vague test."""
    messages = [
        SystemMessage(content=SCREEN_SYSTEM),
        HumanMessage(content=SCREEN_INPUT.format(text=text)),
    ]

    try:
        result: ScreenedText = (
            await llm.get_screen_llm().with_structured_output(ScreenedText).ainvoke(messages)
        )
    except Exception as error:  # noqa: BLE001 - it lets the text through
        logger.warning("The text check failed, so the text goes through: %s", type(error).__name__)

        return True

    return result.testable


async def refuse_if_nothing_to_test(
    text: str, action: str, company_id=None, user_id: str | None = None
) -> None:
    """A 422 when the text names nothing a test could cover (a recipe, a story, gibberish,
    instructions to an AI); its call is traced and priced as part of `action`."""
    async with ai_run(action, company_id=company_id, user_id=user_id):
        testable = await names_something_testable(text)

    if not testable:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, NOTHING_TO_TEST)
