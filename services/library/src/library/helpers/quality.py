from library.constants.feedback import ReportReason
from library.constants.quality import (
    DEAD_OPTION_SHARE,
    DISLIKES_TO_FLAG,
    MIN_ANSWERS,
    MIN_GROUP_ANSWERS,
    MIN_SEPARATION,
    REPORTS_TO_FLAG,
    STRONG_SCORE,
    TOO_EASY_RATE,
    TOO_HARD_RATE,
    TOO_SLOW_SHARE,
    WEAK_SCORE,
    QualityFlag,
)


def wrong_key(options: list[dict], option_picks: dict[str, int]) -> bool:
    """A wrong option is picked more often than one marked correct (for a multi-answer question,
    than the right option ticked least often)."""
    right = min(option_picks.get(option["answer"], 0) for option in options if option["correct"])

    return any(
        option_picks.get(option["answer"], 0) > right for option in options if not option["correct"]
    )


def dead_option(options: list[dict], answers: int, option_picks: dict[str, int]) -> bool:
    return any(
        option_picks.get(option["answer"], 0) < answers * DEAD_OPTION_SHARE
        for option in options
        if not option["correct"]
    )


def score_group(final_score: int | None) -> str | None:
    """A candidate's group on a topic by their score: strong, weak, or None in between."""
    if final_score is None:
        return None

    if final_score >= STRONG_SCORE:
        return "strong"

    return "weak" if final_score <= WEAK_SCORE else None


def no_separation(stats) -> bool:
    """Strong and weak candidates get it right about as often (by credit, for a multi-answer
    question): it says nothing about them."""
    if stats.strong_answers < MIN_GROUP_ANSWERS or stats.weak_answers < MIN_GROUP_ANSWERS:
        return False

    strong = stats.strong_correct / stats.strong_answers
    weak = stats.weak_correct / stats.weak_answers

    return strong - weak < MIN_SEPARATION


def too_slow(stats) -> bool:
    """Time runs out on it too often: too long to read in its time."""
    shown = stats.answers + stats.timeouts

    return shown >= MIN_ANSWERS and stats.timeouts >= shown * TOO_SLOW_SHARE


def difficulty(stats) -> float | None:
    """The share of candidates who answer it right (its difficulty for the integrity signals in
    rounds); None before MIN_ANSWERS answers, when it says nothing yet."""
    if stats is None or stats.answers < MIN_ANSWERS:
        return None

    return round(stats.correct / stats.answers, 3)


def flag_for(
    options: list[dict],
    answers: int,
    correct: float,
    option_picks: dict[str, int],
    reports: dict[str, int],
    likes: int,
    dislikes: int,
    unhelpful: bool = False,
) -> QualityFlag | None:
    """The most serious problem the answers and feedback show, or None. `correct` is the credit
    the answers earned, so too hard and too easy read the average credit of a multi-answer
    question as the share right of a single-answer one. `unhelpful`: it doesn't
    separate strong candidates from weak ones, or it's too slow to read (no_separation,
    too_slow); both ask for a rewrite."""
    answered = answers >= MIN_ANSWERS

    if reports.get(ReportReason.WRONG_ANSWER, 0) >= REPORTS_TO_FLAG or (
        answered and wrong_key(options, option_picks)
    ):
        return QualityFlag.WRONG_KEY

    if (
        reports.get(ReportReason.UNCLEAR, 0) >= REPORTS_TO_FLAG
        or reports.get(ReportReason.HARD_TO_READ, 0) >= REPORTS_TO_FLAG
        or reports.get(ReportReason.OFF_TOPIC, 0) >= REPORTS_TO_FLAG
        or (dislikes >= DISLIKES_TO_FLAG and dislikes >= 2 * likes)
        or (answered and correct <= answers * TOO_HARD_RATE)
        or unhelpful
    ):
        return QualityFlag.REWRITE

    if answered and (
        correct >= answers * TOO_EASY_RATE or dead_option(options, answers, option_picks)
    ):
        return QualityFlag.WEAK_OPTIONS

    return None


def replacement(revision, question, versions) -> tuple[str, list]:
    """The text and options that replaced `revision`: the next kept revision of its question, or
    the question as it is now."""
    following = next(
        (
            version
            for version in versions
            if version.question_id == revision.question_id
            and version.replaced_at > revision.replaced_at
        ),
        None,
    )

    if following is not None:
        return following.text, following.options

    return question.text, question.options
