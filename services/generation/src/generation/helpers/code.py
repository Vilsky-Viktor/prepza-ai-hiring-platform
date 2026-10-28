from generation.constants.code import UNTAGGED_FENCE


def example_of(text: str, fence: str = UNTAGGED_FENCE) -> str:
    """The example in a question's first fence opening with `fence` (by default the first
    untagged one), without its fences."""
    start = text.find(fence) + len(fence)
    end = text.find("```", start)

    return text[start : end if end != -1 else len(text)].strip("\n")
