from prepza_common.config.constants import DEFAULT_LANGUAGE, MAX_INTERVIEW_QUESTIONS
from prepza_common.limits.limits import limit, question_seconds
from prepza_common.redis import memory_cache

from site_content.constants.help import GUIDE_CACHE_SECONDS
from site_content.helpers.help import knowledge
from site_content.helpers.page_guides import guide_text, page_guide
from site_content.integrations import billing
from site_content.integrations.redis import get_redis
from site_content.schemas.help import HelpKnowledgeOut


async def guide_limits(redis) -> dict:
    """The limits the platform guide names, as they are now, so it never contradicts the site."""
    return {
        "max_companies": await limit(redis, "MAX_OWNED_COMPANIES"),
        "interviews_per_day": await limit(redis, "INTERVIEWS_PER_DAY"),
        "interviews_per_day_unpaid": await limit(redis, "INTERVIEWS_PER_DAY_UNPAID"),
        "waiting_interviews": await limit(redis, "MAX_INTERVIEWS_WITHOUT_CANDIDATES"),
        "waiting_interviews_unpaid": await limit(redis, "MAX_INTERVIEWS_WITHOUT_CANDIDATES_UNPAID"),
        "previews_per_day": await limit(redis, "PREVIEWS_PER_COMPANY_DAY"),
        "voice_previews_per_day": await limit(redis, "VOICE_PREVIEWS_PER_COMPANY_DAY"),
        "bias_audit_exports_per_day": await limit(redis, "BIAS_AUDIT_EXPORTS_PER_DAY"),
        "seconds_basic": await question_seconds(redis, "basic"),
        "seconds_medium": await question_seconds(redis, "medium"),
        "seconds_hard": await question_seconds(redis, "hard"),
        "max_interview_questions": MAX_INTERVIEW_QUESTIONS,
    }


async def platform_guide(language: str, country: str | None = None) -> str:
    """The help chat's knowledge with the FAQ in `language` and the prices in the currency of
    `country` (US dollars without one), kept a while in this process."""
    key = f"help:guide:{language}:{country or ''}"
    found = memory_cache.get(key)

    if found is None:
        catalog = await billing.catalog(country)
        found = knowledge(language, catalog, await guide_limits(get_redis()))

        # Without billing's prices, it's made again next time.
        if catalog is not None:
            memory_cache.put(key, found, GUIDE_CACHE_SECONDS)

    return found


async def chat_knowledge(country: str | None, page: str | None) -> HelpKnowledgeOut:
    """What the help chat answers from, in English: the platform guide with the prices in the
    currency of the visitor's `country`, and the guide of the page they ask on (`page`, its
    key) when it's a known one."""
    guide = page_guide(page, DEFAULT_LANGUAGE) if page else None

    return HelpKnowledgeOut(
        knowledge=await platform_guide(DEFAULT_LANGUAGE, country),
        page_guide=guide_text(guide) if guide else None,
    )
