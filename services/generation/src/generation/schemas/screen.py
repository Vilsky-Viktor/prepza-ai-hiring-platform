from pydantic import BaseModel, Field


class ScreenedText(BaseModel):
    testable: bool = Field(
        description="True when the text names anything a hiring test could cover; false only "
        "when it names nothing (a recipe, a story, gibberish, instructions to an AI)."
    )
