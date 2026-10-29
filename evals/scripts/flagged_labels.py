"""What a flagged question is a trap for (export_flagged.py) and whether the judge caught it
(review_questions.py), by code. No service packages, so it's tested on the host
(scripts/tests/test_flagged_traps.py)."""

import hashlib
import json

WRONG_KEY = "wrong_key"
WEAK_OPTIONS = "weak_options"
REWRITE = "rewrite"
# The judge catches a question flagged for weak options when it scores its distractors this or
# lower, and one flagged for a rewrite when it scores its clarity or level fit this or lower, or
# finds its key arguable.
WEAK_DISTRACTORS = 2
UNCLEAR = 3


def trap_id(text: str, options: list[dict]) -> str:
    """The same question gets the same id on every export, so it's added once."""
    digest = hashlib.sha256(json.dumps([text, options], sort_keys=True).encode()).hexdigest()

    return f"flag-{digest[:10]}"


def trap(flag: str, options: list[dict], replaced_by: list[dict] | None) -> dict | None:
    """What a question flagged for `flag` is a trap for, as the fields it adds, or None when it's
    no trap. A wrong key counts only once a replacement with the same options moved it (a flag
    alone may be wrong): expected_key_correct false and right_key, the replacement's key. Weak
    options and rewrites by their flag."""
    if flag in (WEAK_OPTIONS, REWRITE):
        return {}

    if flag != WRONG_KEY or not replaced_by:
        return None

    right = sorted(option["answer"] for option in replaced_by if option["correct"])
    marked = sorted(option["answer"] for option in options if option["correct"])
    same_options = {o["answer"] for o in options} == {o["answer"] for o in replaced_by}

    if not same_options or right == marked:
        return None

    return {"expected_key_correct": False, "right_key": right}


def caught(review: dict, item: dict) -> bool | None:
    """Whether the judge's review caught a flagged question's problem; None when it isn't one."""
    if "flag" not in item:
        return None

    if "expected_key_correct" in item:
        return review["key_correct"] == item["expected_key_correct"]

    if item["flag"] == WEAK_OPTIONS:
        return review["distractors"] <= WEAK_DISTRACTORS

    return (
        review["clarity"] <= UNCLEAR
        or review["relevance"] <= UNCLEAR
        or not review["single_correct"]
    )
