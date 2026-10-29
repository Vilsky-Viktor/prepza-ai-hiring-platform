"""An answer voted down in one shape, from a Langfuse trace's model calls
(evals/scripts/disliked_shape.py)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evals" / "scripts"))

from disliked_shape import disliked, exchange


def call(at: int, asked: str, written) -> tuple:
    """A model call as Langfuse gives it: its input and output as JSON text."""
    given = [{"role": "system", "content": "Rules"}, {"role": "user", "content": asked}]

    return at, json.dumps(given), json.dumps({"role": "assistant", "content": written})


def test_the_question_and_answer_come_from_the_traces_last_model_call():
    calls = [
        call(
            2, "Who passed?", [{"type": "text", "text": "Ann "}, {"type": "text", "text": "did."}]
        ),
        # An earlier call that chose a tool, read out of order.
        call(1, "Who passed?", ""),
    ]

    assert exchange(calls) == ("Who passed?", "Ann \ndid.")


def test_a_trace_without_calls_or_text_gives_none():
    assert exchange([]) == (None, None)
    assert exchange([(1, "not json", "")]) == (None, None)


def test_every_source_has_the_same_shape():
    help_chat = disliked("help", "a" * 32, "2026-10-29", None, None)
    assistant = disliked("assistant", None, "2026-10-29", "Who passed?", "Ann did.")

    assert help_chat.keys() == assistant.keys()
