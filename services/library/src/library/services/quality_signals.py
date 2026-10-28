from collections import Counter
from datetime import UTC, datetime, timedelta

from library.constants.quality import MAX_PATTERN_SIGNALS
from library.core.db import Session
from library.helpers.quality import flag_for, replacement
from library.repositories import quality_signals
from library.schemas.quality_report import QualitySignalOut


async def flagged(since: datetime) -> list[QualitySignalOut]:
    async with Session() as session:
        found = await quality_signals.flagged_since(session, since, MAX_PATTERN_SIGNALS)
        ids = [question.id for question, _ in found]
        reasons, votes = await quality_signals.feedback(session, ids)

    return [
        QualitySignalOut(
            flag=stats.flag,
            text=question.text,
            options=question.options,
            answers=stats.answers,
            correct=stats.correct,
            option_picks=stats.option_picks,
            timeouts=stats.timeouts,
            reasons=reasons.get(question.id, {}),
            likes=votes.get(question.id, (0, 0))[0],
            dislikes=votes.get(question.id, (0, 0))[1],
        )
        for question, stats in found
    ]


async def replaced(since: datetime) -> list[QualitySignalOut]:
    """Replaced questions with the flag they had, or, for revisions kept before flags were
    kept with them, the flag their answers and feedback give; an owner's edit of a question
    nothing was wrong with is left out."""
    async with Session() as session:
        found = await quality_signals.replaced_since(session, since, MAX_PATTERN_SIGNALS)
        ids = {revision.question_id for revision, _ in found}
        versions = await quality_signals.revisions_of(session, ids)

    signals = []

    for revision, question in found:
        reasons = dict(Counter(report["reason"] for report in revision.reports))
        flag = revision.flag or flag_for(
            revision.options,
            revision.answers,
            revision.correct,
            revision.option_picks,
            reasons,
            revision.likes,
            revision.dislikes,
        )

        if flag is None:
            continue

        new_text, new_options = replacement(revision, question, versions)
        signals.append(
            QualitySignalOut(
                flag=flag,
                text=revision.text,
                options=revision.options,
                answers=revision.answers,
                correct=revision.correct,
                option_picks=revision.option_picks,
                timeouts=0,
                reasons=reasons,
                likes=revision.likes,
                dislikes=revision.dislikes,
                new_text=new_text,
                new_options=new_options,
            )
        )

    return signals


async def recent(days: int) -> list[QualitySignalOut]:
    """Questions flagged or replaced in the last `days`, across every company and template."""
    since = datetime.now(UTC) - timedelta(days=days)

    return await flagged(since) + await replaced(since)
