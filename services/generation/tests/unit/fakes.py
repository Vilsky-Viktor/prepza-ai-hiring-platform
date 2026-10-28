"""Fakes shared by the unit tests that write questions: the model's question items, single- or
multi-answer, and a verifier that answers the self-check of a new multi-answer question."""

import re

from generation.schemas.questions import QuestionItem, QuestionItemList
from generation.schemas.verify import SelfCheck

# A single-answer question's options, and a multi-answer one's: right ones start with "Right".
SINGLE = (["Right"], ["W1", "W2", "W3"])
MULTI = (["Right 1", "Right 2"], ["W1", "W2"])
# A written question's options, as the pipeline stores them.
OPTIONS = [{"answer": "Right", "correct": True}, {"answer": "Wrong", "correct": False}]
MULTI_OPTIONS = [*OPTIONS, {"answer": "Also right", "correct": True}]
# An example as a written question's text ends with it, in a notation the site colors.
EXAMPLE = "\n```python\nprint(1)\n```"
ASKED_MULTI = re.compile(r"write (\d+) as select-all-that-apply")
ASKED_EXAMPLES = re.compile(r"exactly (\d+) of the \d+ come with an example")
OPTION_LINE = re.compile(r"^(\d+)\. (.+)$", re.MULTILINE)


def question_item(text: str, multi: bool = False, example: bool = False) -> QuestionItem:
    correct, distractors = MULTI if multi else SINGLE

    return QuestionItem(
        question=text,
        example="print(1)" if example else None,
        example_language="python" if example else None,
        correct_options=correct,
        distractors=distractors,
        ambiguous=False,
    )


def asked_multi(prompt: str) -> int:
    """How many multi-answer questions a question prompt asks for."""
    return int(ASKED_MULTI.search(prompt).group(1))


def asked_examples(prompt: str) -> int:
    """How many questions with an example a question prompt asks for."""
    return int(ASKED_EXAMPLES.search(" ".join(prompt.split())).group(1))


def items(texts: list[str], multi: int = 0, examples: int = 0) -> QuestionItemList:
    """The questions, the first `multi` of them multi-answer and the last `examples` with an
    example."""
    return QuestionItemList(
        items=[
            question_item(text, index < multi, index >= len(texts) - examples)
            for index, text in enumerate(texts)
        ]
    )


class FakeVerifier:
    """The verifier: names the options shown that start with "Right"; `open_condition` names a
    condition left open, `error` makes every call fail."""

    def __init__(self, open_condition=None, error=False):
        self.open_condition = open_condition
        self.error = error
        self.prompts = []

    def with_structured_output(self, schema):
        return self

    async def ainvoke(self, messages):
        prompt = messages[-1].content
        self.prompts.append(prompt)

        if self.error:
            raise ConnectionError("OpenAI is down")

        shown = OPTION_LINE.findall(prompt.split("Options")[-1])
        right = [int(number) for number, answer in shown if answer.startswith("Right")]

        return SelfCheck(correct_indexes=right, open_condition=self.open_condition)
