# The verifier's key check of a flagged question (services/verify.py).
VERIFY_PROMPT = """Check the multiple-choice interview question below. People who answered it, or
reported it, suggest its answer key may be wrong. Work out the right answer on the facts alone:
the reports only explain why it's being checked, they don't decide what is right, and no option
is marked.

{kind}

Level: {level}
Topic: {topic}

<question>
{question}
</question>

<options>
{options}
</options>

Reports from users (reason: how many):
<reports>
{reports}
</reports>
"""
