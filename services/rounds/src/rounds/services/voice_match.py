from prepza_common.ai.llm import call_cost
from prepza_common.ai.tracing import traced_call

from rounds.config import settings
from rounds.constants.voice import MATCH_ACTION, Intent
from rounds.helpers.voice_match import is_noise, match_prompt, obvious, understood
from rounds.integrations import llm
from rounds.schemas.rounds import NextQuestion
from rounds.schemas.voice import VoiceMatch


async def read_match(
    question: NextQuestion, said: str, waiting: list[int], language: str
) -> tuple[VoiceMatch | None, dict]:
    """The model's reading of a spoken answer (None when it gave none) and the call's usage."""
    result = (
        await llm.get_match_model()
        .with_structured_output(VoiceMatch, include_raw=True, strict=True)
        .ainvoke(match_prompt(question, said, waiting, language))
    )

    return result["parsed"], (result["raw"].usage_metadata or {})


async def match(
    question: NextQuestion, said: str, waiting: list[int], language: str, session_id: str
) -> tuple[Intent, list[int], dict | None]:
    """What the candidate meant and the options it picks (helpers/voice_match.py understood), with
    the call's usage. No words at all (a cough, a knock) is noise, and a plain yes or a letter
    alone is read by code, both without a call (usage None). The trace gets the call's tokens,
    cost and reading under the session's id, never the candidate's words or the question."""
    if is_noise(said):
        return Intent.NOISE, [], None

    plain = obvious(said, question, waiting, language)

    if plain is not None:
        return *plain, None

    parsed, usage = await read_match(question, said, waiting, language)
    model = settings.voice_match_model
    reading = parsed.model_dump(mode="json") if parsed else None
    traced_call(
        MATCH_ACTION, [MATCH_ACTION], session_id, model, usage, call_cost(model, usage), reading
    )

    if parsed is None:
        return Intent.UNCLEAR, [], usage

    intent, picks = understood(parsed, question.multi, waiting)

    return intent, picks, usage
