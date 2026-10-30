from generation.constants.bank import CONTACT_DETAILS


def bank_text(topic: str, text: str, options: list[str]) -> str:
    """What the filter reads of a question: its topic, its text and its options, one a line."""
    lines = [f"Topic: {topic}", f"Question: {text}", *(f"- {option}" for option in options)]

    return "\n".join(lines)


def has_contact_details(text: str) -> bool:
    """An email or web address anywhere in the text: never general, whatever the model says."""
    return any(pattern.search(text) for pattern in CONTACT_DETAILS)
