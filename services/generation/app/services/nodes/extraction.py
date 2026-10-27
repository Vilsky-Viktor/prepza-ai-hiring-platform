from langchain_core.messages import HumanMessage, SystemMessage
from prepza_common.config.constants import MAX_TITLE_LENGTH

from app.helpers.prompts import language_name
from app.integrations import llm
from app.models.state import State
from app.prompts.extraction import (
    COMPANY_TEST,
    EXTRACTION_INPUT,
    EXTRACTION_SYSTEM,
    TEMPLATE_TEST,
)
from app.schemas.extraction import JobExtraction
from app.storage import draft_cache


async def extract_info(state: State) -> dict:
    """Title, requirements and level; the same pasted text reuses its earlier result."""
    # A template never tells which company's posting it came from.
    request = EXTRACTION_INPUT.format(
        posting=state["input_text"],
        kind=TEMPLATE_TEST if state.get("template") else COMPANY_TEST,
        language=language_name(state.get("language")),
    )
    source = EXTRACTION_SYSTEM + request
    model = llm.get_generation_llm()
    extracted = await draft_cache.get("extraction", source, model)

    if extracted is None:
        result: JobExtraction = await model.with_structured_output(JobExtraction).ainvoke(
            [SystemMessage(content=EXTRACTION_SYSTEM), HumanMessage(content=request)]
        )
        extracted = {
            "title": result.title,
            "requirements": result.requirements,
            "level": result.level,
        }
        await draft_cache.put("extraction", source, extracted, model)

    # A title the model made too long (now or in the cache) is cut to what editing it allows,
    # so saving the paid-for questions never fails on it.
    return {**extracted, "title": extracted["title"][:MAX_TITLE_LENGTH].strip()}
