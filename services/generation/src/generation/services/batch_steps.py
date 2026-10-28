# What a piece of batch work asks the model (`body_for`) and what its reply leads to (`advance`):
# its result, its next call, or giving up. The same prompts, schemas and checks as the direct
# calls (news.py, campaigns.py, answers.py, regenerate.py), so a batch writes what they would.
from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from generation.config import settings
from generation.constants.batch_work import BATCH_WORK_ATTEMPTS, BatchKind, BatchStep
from generation.helpers.questions import normalize, with_example
from generation.integrations.openai_batch import request_body
from generation.prompts.campaigns import CAMPAIGN_TRANSLATION_SYSTEM
from generation.prompts.news import NEWS_TRANSLATION_SYSTEM
from generation.schemas.campaigns import CampaignSource, TranslatedCampaign
from generation.schemas.news import NewsSource, TranslatedNews
from generation.schemas.questions import AnswerList, NewQuestion
from generation.schemas.regenerate import QuestionContext
from generation.services.answers import answers_messages, options_of
from generation.services.campaigns import campaign_limits, campaign_request, without_made_up_button
from generation.services.news import LIMITS as NEWS_LIMITS
from generation.services.news import news_request
from generation.services.regenerate import accepted, question_messages
from generation.services.translations import checked


@dataclass
class Advance:
    """What a reply leads to: `result` when the work is done, else the next `step` and its
    `payload`; `give_up` when it has had its attempts."""

    result: object = None
    step: str | None = None
    payload: dict = field(default_factory=dict)
    give_up: bool = False


def body_for(kind: str, step: str, payload: dict) -> dict:
    """The chat completion a step sends, as its direct call would make it."""
    if kind == BatchKind.NEWS:
        source = NewsSource(**payload["source"])
        messages = [
            SystemMessage(content=NEWS_TRANSLATION_SYSTEM),
            HumanMessage(content=news_request(source, payload["language"])),
        ]

        return translation_body(messages, TranslatedNews)

    if kind == BatchKind.CAMPAIGN:
        source = CampaignSource(**payload["source"])
        messages = [
            SystemMessage(content=CAMPAIGN_TRANSLATION_SYSTEM),
            HumanMessage(content=campaign_request(source, payload["language"])),
        ]

        return translation_body(messages, TranslatedCampaign)

    context = QuestionContext(**payload["context"])

    if step == BatchStep.QUESTION:
        messages = question_messages(context, payload["reasons"], payload["existing"])

        return writing_body(messages, NewQuestion)

    return writing_body(answers_messages(answer_task(context, payload["text"]), [0]), AnswerList)


def translation_body(messages, schema: type[BaseModel]) -> dict:
    model, effort = settings.translation_model, settings.translation_reasoning_effort

    return request_body(model, effort, messages, schema)


def writing_body(messages, schema: type[BaseModel]) -> dict:
    model, effort = settings.interview_model, settings.interview_reasoning_effort

    return request_body(model, effort, messages, schema)


def answer_task(context: QuestionContext, text: str) -> dict:
    return {
        "topic_index": 0,
        "topic": context.topic,
        "start": 0,
        "questions": [text],
        "level": context.level,
        "language": context.language,
        "multi": context.multi,
    }


def parsed[T: BaseModel](schema: type[T], reply: str | None) -> T | None:
    try:
        return schema.model_validate_json(reply) if reply else None
    except ValidationError:
        return None


async def advance(kind: str, step: str, attempt: int, payload: dict, reply: str | None) -> Advance:
    """What `reply` to the step's call leads to. An unusable reply asks again, until the work
    has had BATCH_WORK_ATTEMPTS replies."""
    found = await next_of(kind, step, payload, reply)

    if found.result is None and attempt + 1 >= BATCH_WORK_ATTEMPTS:
        return Advance(give_up=True)

    return found


async def next_of(kind: str, step: str, payload: dict, reply: str | None) -> Advance:
    if kind in (BatchKind.NEWS, BatchKind.CAMPAIGN):
        return translated(kind, payload, reply)

    if step == BatchStep.QUESTION:
        return await written(payload, reply)

    return with_options(payload, reply)


def translated(kind: str, payload: dict, reply: str | None) -> Advance:
    """A translation within its limits is done; one that isn't is asked for again."""
    news = kind == BatchKind.NEWS
    result = parsed(TranslatedNews if news else TranslatedCampaign, reply)
    source = (NewsSource if news else CampaignSource)(**payload["source"])
    limits = NEWS_LIMITS if news else campaign_limits(source)

    try:
        translation = checked(result, limits, payload["language"]) if result else None
    except ValueError:
        translation = None

    if translation is None:
        return Advance(step=BatchStep.TRANSLATE, payload=payload)

    return Advance(result=translation if news else without_made_up_button(source, translation))


async def written(payload: dict, reply: str | None) -> Advance:
    """A new question that can replace the old one goes on to its options; one that can't is
    asked for again, unlike it too."""
    result = parsed(NewQuestion, reply)
    existing = payload["existing"]

    if result is None:
        return Advance(step=BatchStep.QUESTION, payload=payload)

    context = QuestionContext(**payload["context"]).model_copy(update={"existing": existing})
    text = await accepted(context, result, {normalize(item) for item in existing})

    if not text:
        tried = with_example(result.question, result.example, result.example_language)

        return Advance(step=BatchStep.QUESTION, payload={**payload, "existing": [*existing, tried]})

    return Advance(step=BatchStep.OPTIONS, payload={**payload, "text": text})


def with_options(payload: dict, reply: str | None) -> Advance:
    """Options for the question are the result; a question the model found ambiguous is
    replaced by a new one (never offered again), and an incomplete answer is asked again."""
    result = parsed(AnswerList, reply)
    multi = QuestionContext(**payload["context"]).multi
    options = options_of(result, [0], multi).get(0) if result else None

    if options:
        return Advance(result=(payload["text"], options))

    if options is None:
        return Advance(step=BatchStep.OPTIONS, payload=payload)

    existing = [*payload["existing"], payload["text"]]

    return Advance(step=BatchStep.QUESTION, payload={**payload, "existing": existing})
