"""The eval gate's decision (pattern_gate.py), by code: each dimension of a set with its 95%
interval, and whether the rule ships: its mistake rarer beyond the noise, nothing else worse
beyond it. No model packages, so it's tested on the host (scripts/tests/test_eval_gate.py)."""

from common import is_multi
from stats import mean_interval, wilson

# Each dimension: its name, whether it's a share (else a mean), and whether higher is better.
DIMENSIONS = (
    ("keys_single", True, True),
    ("keys_multi", True, True),
    ("clarity", False, True),
    ("level_fit", False, True),
    ("distractors", False, True),
    ("seconds", False, False),
    ("mistake", True, False),
)


def measures(items: list[dict], reviews: list[dict], mistakes: list[bool]) -> dict:
    """Each dimension's value with its 95% interval, as (value, low, high); None when the set
    has too few to tell (no multi-answer question, one question)."""
    single = [r for r, item in zip(reviews, items) if not is_multi(item)]
    multi = [r for r, item in zip(reviews, items) if is_multi(item)]

    def counted(hits: list[bool]):
        return wilson(sum(hits), len(hits)) if hits else None

    def averaged(values: list[float]):
        return mean_interval(values) if len(values) > 1 else None

    return {
        "keys_single": counted([r["key_correct"] for r in single]),
        "keys_multi": counted([r["key_correct"] for r in multi]),
        "clarity": averaged([r["clarity"] for r in reviews]),
        "level_fit": averaged([r["relevance"] for r in reviews]),
        "distractors": averaged([r["distractors"] for r in reviews]),
        "seconds": averaged([r["seconds"] for r in reviews]),
        "mistake": counted(mistakes),
    }


def beyond(a: tuple, b: tuple) -> bool:
    """Two values differ beyond the noise: each lies outside the other's interval."""
    return not b[1] <= a[0] <= b[2] and not a[1] <= b[0] <= a[2]


def decision(without: dict, with_rule: dict) -> tuple[bool, list[str]]:
    """Whether the rule ships, and why not: its mistake must be rarer beyond the noise and no
    other dimension worse beyond it."""
    reasons = []
    before, after = without["mistake"], with_rule["mistake"]

    if before is None or after is None or not (after[0] < before[0] and beyond(after, before)):
        reasons.append("its mistake isn't rarer beyond the noise")

    for name, _, higher in DIMENSIONS:
        before, after = without[name], with_rule[name]

        if name == "mistake" or before is None or after is None:
            continue

        worse = after[0] < before[0] if higher else after[0] > before[0]

        if worse and beyond(after, before):
            reasons.append(f"{name} is worse beyond the noise")

    return not reasons, reasons


def shown(value: tuple | None, is_share: bool) -> str:
    """A dimension as the README writes it: a share in % or a mean, with its interval."""
    if value is None:
        return "-"

    if is_share:
        return f"{100 * value[0]:.1f}% ({100 * value[1]:.1f}-{100 * value[2]:.1f})"

    return f"{value[0]:.2f} ± {value[0] - value[1]:.2f}"
