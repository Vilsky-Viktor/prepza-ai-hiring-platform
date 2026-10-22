# A second, blind look before a key moves: no option is marked and they come in a new order, so
# the answer can't lean on the first check's or on a position.
CONFIRM_PROMPT = """Answer the multiple-choice interview question below on the facts alone.

{kind}

Level: {level}
Topic: {topic}

<question>
{question}
</question>

<options>
{options}
</options>
"""
