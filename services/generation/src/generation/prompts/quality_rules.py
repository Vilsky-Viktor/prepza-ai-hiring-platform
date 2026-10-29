# The rules in use: recurring mistakes found in flagged questions (the weekly pattern job), each
# approved in the admin zone and kept only after the eval gate showed it makes its mistake rarer
# with nothing else worse (evals/scripts/pattern_gate.py; the run in evals/baselines/generation.md
# and on the pattern). Word for word as the pattern says it, so it stays domain-neutral. Rendered
# into the question rules (question_rules.LEARNED_RULES); reviewed and removed like any other
# prompt text.
QUALITY_RULES: tuple[str, ...] = ()
