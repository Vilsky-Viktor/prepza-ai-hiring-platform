from prepza_common.events.campaigns import CAMPAIGN_TRANSLATED
from prepza_common.events.news import NEWS_TRANSLATED

from generation.constants.batch_work import BatchKind
from generation.constants.events import GENERATION_FAILED
from generation.constants.kinds import GenerationKind
from generation.models.batch_work import BatchWork
from generation.models.generation import Generation


def failed_event(generation: Generation) -> tuple[str, dict] | None:
    """Companies hears of a failed interview generation; a template has no interview to tell."""
    if generation.kind != GenerationKind.INTERVIEW:
        return None

    return GENERATION_FAILED, {"generation_id": str(generation.id)}


def translation_event(work: BatchWork, result) -> tuple[str, dict]:
    """A translation as the event its post's or campaign's owner saves it from, with the English
    it's of, so the owner drops it if the text changed since."""
    source = work.payload["source"]
    translations = {work.key: result.model_dump()}

    if work.kind == BatchKind.NEWS:
        data = {"news_id": str(work.subject_id), "title": source["title"], "text": source["text"]}

        return NEWS_TRANSLATED, data | {"translations": translations}

    data = {
        "campaign_id": str(work.subject_id),
        "subject": source["subject"],
        "text": source["text"],
        "button": source["button"],
    }

    return CAMPAIGN_TRANSLATED, data | {"translations": translations}
