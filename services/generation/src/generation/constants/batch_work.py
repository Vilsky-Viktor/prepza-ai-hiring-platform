from enum import StrEnum


class BatchKind(StrEnum):
    """Work that waits on nobody and goes through OpenAI's Batch API at half price: a post's or
    a campaign's translation into one language, new options for a question, a rewritten
    question."""

    NEWS = "news"
    CAMPAIGN = "campaign"
    NEW_OPTIONS = "new_options"
    REWRITE = "rewrite"


class BatchStep(StrEnum):
    """The call a piece of batch work waits on: a translation, a new question, its options."""

    TRANSLATE = "translate"
    QUESTION = "question"
    OPTIONS = "options"


# Pieces of work sent in one batch; the rest go in the next run's.
MAX_BATCH_WORK = 500
# Replies one piece may get before it's given up (a question that keeps coming out unusable,
# a translation that keeps running past its limits). A rewrite's question and options count
# together, as the direct rewrite tries each REGENERATE_ATTEMPTS times.
BATCH_WORK_ATTEMPTS = 6
