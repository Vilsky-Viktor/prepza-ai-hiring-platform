def escape_like(text: str) -> str:
    """The text matched as typed: % and _ aren't wildcards."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
