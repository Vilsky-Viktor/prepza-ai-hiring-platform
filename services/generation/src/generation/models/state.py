import operator
from typing import Annotated

from typing_extensions import TypedDict


class Topic(TypedDict):
    main_topic: str
    subtopics: list[str]


class QuestionTask(TypedDict):
    """Payload for one parallel generate_questions branch: one call for a topic's subtopic."""

    topic_index: int
    topic: str
    # The branch's place within its topic, so merging keeps a stable order.
    subtopic_index: int
    subtopic: str
    count: int
    # How many of `count` are multi-answer ("select all that apply").
    multi: int
    # How many of `count` come with an example when the subtopic is about material in a formal
    # notation (prepza_common.ai.examples).
    examples: int
    level: str
    # Questions the topic already has, reused from other tests.
    existing: list[str]
    # Which angle this call mostly asks about.
    focus: str
    language: str


class AnswerTask(TypedDict):
    """Questions that need options: a re-generated question, or new options for one."""

    topic_index: int
    topic: str
    start: int
    questions: list[str]
    level: str
    language: str
    # Select-all-that-apply questions: every question keeps its kind.
    multi: bool


class FillTask(TypedDict):
    """Payload for one parallel fill_topic branch: one topic short of its size."""

    # The topic's place in `final`, so joining keeps the topic order.
    topic_index: int
    # The topic as collect_results left it ({"topic", "subtopics", "questions", ...}).
    item: dict
    topic_size: int
    multi_share: float
    level: str
    language: str | None


class State(TypedDict):
    input_text: str
    # The code of the language content is written in (prepza_common.config.constants.LANGUAGES).
    language: str
    # A template (public practice): extraction leaves out anything naming the company.
    template: bool
    # The interview's company (None for a template): reuse offers it the shared bank's questions,
    # never its own. Runs started before it was kept have none.
    company_id: str | None
    # Questions each topic gets, from Controls as the run started, so the whole run holds one.
    topic_size: int
    title: str
    requirements: list[str]
    level: str
    topics: list[Topic]
    approved: bool
    # Free-text instructions from the reviewer; empty means approved.
    feedback: str
    # Parallel branches append here; operator.add merges the lists.
    question_pool: Annotated[list[dict], operator.add]
    # Merged {"text", "options"} per topic, indexed by topic index.
    topic_questions: list[list[dict]]
    # Per topic, in the topic order: its embedding, and questions reused as they are.
    topic_embeddings: list[list[float]]
    reused: list[list[dict]]
    # The share of each topic's questions that are multi-answer, as it was when the questions
    # started (prepza_common.ai.multi_answer.multi_share), so the whole run holds one.
    multi_share: float
    final: list[dict]
    # Fill branches append {"topic_index", "item"} here; operator.add merges the lists, and a
    # retry re-runs only the branches that failed.
    filled: Annotated[list[dict], operator.add]
