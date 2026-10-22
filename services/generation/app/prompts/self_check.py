# The self-check of a new select-all-that-apply question, before it's kept: a blind answer, as
# CONFIRM_PROMPT's, and whether the question leaves open a condition that decides an option.
SELF_CHECK_PROMPT = """Answer the select-all-that-apply interview question below on the facts
alone, then check whether it can be answered with certainty.

{kind}

Then return open_condition: a few words naming a condition the question leaves unstated that
decides whether some option is right or wrong, so the option could flip under one reasonable
reading and not another: the standard, law, framework or version in use; which substance,
target, party, role, object or value in the scenario is meant; the order or timing of events;
a region or register of a language; or a case such as two values being equal. Null when every
such condition is stated or no reasonable reading flips an option.

Level: {level}
Topic: {topic}

<question>
{question}
</question>

<options>
{options}
</options>
"""
