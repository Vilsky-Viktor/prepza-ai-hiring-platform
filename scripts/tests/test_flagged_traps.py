"""What a flagged question is a trap for, and whether the judge caught it
(evals/scripts/flagged_labels.py)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evals" / "scripts"))

from flagged_labels import caught, trap, trap_id

OPTIONS = [{"answer": "a", "correct": True}, {"answer": "b", "correct": False}]
MOVED = [{"answer": "a", "correct": False}, {"answer": "b", "correct": True}]
REWRITTEN = [{"answer": "c", "correct": True}, {"answer": "d", "correct": False}]


@pytest.mark.parametrize(
    ("flag", "replaced_by", "expected"),
    [
        # A wrong key counts once a replacement with the same options moved it.
        ("wrong_key", MOVED, {"expected_key_correct": False, "right_key": ["b"]}),
        # A flag alone may be wrong; a kept key or new options settle nothing about the old key.
        ("wrong_key", None, None),
        ("wrong_key", OPTIONS, None),
        ("wrong_key", REWRITTEN, None),
        ("weak_options", None, {}),
        ("rewrite", REWRITTEN, {}),
        ("unknown", None, None),
    ],
)
def test_a_flagged_question_is_a_trap_only_for_what_is_known_about_it(flag, replaced_by, expected):
    assert trap(flag, OPTIONS, replaced_by) == expected


def test_the_same_question_gets_the_same_id_on_every_export():
    assert trap_id("Q?", OPTIONS) == trap_id("Q?", [dict(o) for o in OPTIONS])
    assert trap_id("Q?", OPTIONS) != trap_id("Q?", MOVED)


@pytest.mark.parametrize(
    ("item", "review", "expected"),
    [
        ({"flag": "wrong_key", "expected_key_correct": False}, {"key_correct": False}, True),
        ({"flag": "wrong_key", "expected_key_correct": False}, {"key_correct": True}, False),
        ({"flag": "weak_options"}, {"distractors": 2}, True),
        ({"flag": "weak_options"}, {"distractors": 3}, False),
        ({"flag": "rewrite"}, {"clarity": 3, "relevance": 5, "single_correct": True}, True),
        ({"flag": "rewrite"}, {"clarity": 5, "relevance": 5, "single_correct": False}, True),
        ({"flag": "rewrite"}, {"clarity": 4, "relevance": 4, "single_correct": True}, False),
        ({}, {"key_correct": True}, None),
    ],
)
def test_the_judge_catches_a_flagged_question_when_it_finds_its_flags_problem(
    item, review, expected
):
    assert caught(review, item) == expected
