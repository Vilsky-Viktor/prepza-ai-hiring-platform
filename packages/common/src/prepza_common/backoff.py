import random


def wait_seconds(first: float, attempt: int) -> float:
    """How long to wait before retry number `attempt` (0 for the first retry): exponential from
    `first`, with full jitter, so callers that failed together don't all retry together."""
    return random.uniform(0, first * 2**attempt)
