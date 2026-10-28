"""Imports go one way, and repositories never commit (python-services.md; the check is the
shared tests' layer_rules)."""

from pathlib import Path

from layer_rules import layer_problems

PACKAGE = Path(__file__).resolve().parents[2] / "src" / "generation"


def test_the_layers_keep_their_rules():
    assert layer_problems(PACKAGE) == []
