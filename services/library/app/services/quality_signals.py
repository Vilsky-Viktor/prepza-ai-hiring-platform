from collections import Counter
from datetime import UTC, datetime, timedelta

from app.constants.quality import MAX_PATTERN_SIGNALS
from app.helpers.quality import flag_for
from app.schemas.quality_report import QualitySignalOut
from app.storage import quality_signals
from app.storage.quality_report import replacement


async def flagged(since: datetime) -> list[QualitySignalOut]:
    found = await quality_signals.flagged_since(since, MAX_PATTERN_SIGNALS)
    reasons, votes = await quality_signals.feedback([question.id for question, _ in found])

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
    found = await quality_signals.replaced_since(since, MAX_PATTERN_SIGNALS)
    versions = await quality_signals.revisions_of({revision.question_id for revision, _ in found})
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
