from pydantic import BaseModel, Field

from generation.constants.code import CodeLanguage
from generation.constants.generation import MAX_OPTION_CHARS, OPTIONS

EXAMPLE = (
    "What the question shows, such as instructions, a lookup, a command, a formula or a file, "
    "exactly as it would be typed, with real line breaks and indentation and without a Markdown "
    "fence; when it acts on stored records, those few records first. Only the lines the answer "
    "depends on, one piece unless the question is about several working together. Null when the "
    'question shows none. Never null when the question refers to one, such as "these lines" or '
    '"the file below". At most 8 short lines.'
)
EXAMPLE_LANGUAGE = (
    "The notation the example is written in, for its colors. One that shows several files gets "
    'the notation most of it is written in, never "text". "text" only for one in no listed '
    "notation, such as a table's rows or plain prose. Null when there is no example."
)


CORRECT_OPTIONS = (
    "The correct options: exactly one for a single-answer question; 2 or 3 for a "
    "select-all-that-apply question, never all of them. Each as concise as possible while complete "
    f"and accurate, never longer than {MAX_OPTION_CHARS} characters."
)
DISTRACTORS_TEXT = (
    f"The incorrect options, so that there are {OPTIONS} options in all, each at most "
    f"{MAX_OPTION_CHARS} characters, plausible, in the same form as the correct ones and about "
    "as long, never noticeably shorter."
)
AMBIGUOUS = (
    "True if the key could be argued: for a single-answer question, more than one option could "
    "be defended as correct; for a select-all-that-apply one, any option could be defended as "
    "correct and as incorrect alike. The question is then dropped."
)


class QuestionItem(BaseModel):
    question: str = Field(
        description="The question itself in one or two short, plain sentences of at most 40 words "
        "(50 for a hard one), without numbering, listed choices or the example."
    )
    example: str | None = Field(description=EXAMPLE)
    example_language: CodeLanguage | None = Field(description=EXAMPLE_LANGUAGE)
    correct_options: list[str] = Field(description=CORRECT_OPTIONS)
    distractors: list[str] = Field(description=DISTRACTORS_TEXT)
    ambiguous: bool = Field(description=AMBIGUOUS)


class QuestionItemList(BaseModel):
    items: list[QuestionItem] = Field(description="Distinct questions, each with its options.")


class NewQuestion(BaseModel):
    question: str = Field(
        description="One new interview question in one or two short, plain sentences of at most "
        "40 words (50 for a hard one), without numbering or the example."
    )
    example: str | None = Field(description=EXAMPLE)
    example_language: CodeLanguage | None = Field(description=EXAMPLE_LANGUAGE)


class AnswerItem(BaseModel):
    id: int = Field(description="The id of the question being answered, copied exactly.")
    correct_options: list[str] = Field(description=CORRECT_OPTIONS)
    distractors: list[str] = Field(description=DISTRACTORS_TEXT)
    ambiguous: bool = Field(description=AMBIGUOUS)


class AnswerList(BaseModel):
    answers: list[AnswerItem] = Field(description="One item per question id provided.")
