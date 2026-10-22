# One call of the tag_code_languages job: the notation each of a batch of examples is written in.
from langchain_core.messages import HumanMessage

from app.integrations import llm
from app.prompts.code_languages import CODE_LANGUAGES_PROMPT
from app.schemas.code import CodeTagList


async def tag_examples(examples: list[str]) -> dict[int, str]:
    """Each example's notation by its index in `examples`; one the model skipped, or a number it
    made up, is missing."""
    numbered = "\n\n".join(f"{index}.\n{example}" for index, example in enumerate(examples))
    result: CodeTagList = (
        await llm.get_code_tags_llm()
        .with_structured_output(CodeTagList)
        .ainvoke([HumanMessage(content=CODE_LANGUAGES_PROMPT.format(examples=numbered))])
    )

    return {item.id: item.language for item in result.items if 0 <= item.id < len(examples)}
