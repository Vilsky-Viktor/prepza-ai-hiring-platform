"""Imports go one way, handlers reach the database through services, and repositories never
commit (python-services.md; the check is the shared tests' layer_rules)."""

from pathlib import Path

from layer_rules import layer_problems

PACKAGE = Path(__file__).resolve().parents[2] / "src" / "companies"


def test_the_layers_keep_their_rules():
    assert layer_problems(PACKAGE) == []
