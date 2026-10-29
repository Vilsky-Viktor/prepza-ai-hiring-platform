# The AI-trap pick: a question asked as a candidate would paste it into an AI app, with no role
# and no hint that it's checked, so the model answers as it does for them. The eval's own prompt:
# generation has no pick step, as the eval found no traps the planned way (evals/README.md).
AI_PICK_PROMPT = """Which option is correct?{note}

{question}

{options}
"""

MULTI_NOTE = " Select all that apply."
