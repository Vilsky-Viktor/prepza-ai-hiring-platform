from pydantic import BaseModel, Field

from generation.constants.code import CodeLanguage


class CodeTag(BaseModel):
    id: int = Field(description="The example's number, copied exactly.")
    language: CodeLanguage = Field(
        description='The example\'s language; "text" for one in no listed language.'
    )


class CodeTagList(BaseModel):
    items: list[CodeTag] = Field(description="One entry for each example.")
