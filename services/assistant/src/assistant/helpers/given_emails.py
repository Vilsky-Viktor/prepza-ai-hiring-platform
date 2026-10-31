import re

from testee_common.config.constants import EMAIL_PATTERN

EMAIL = re.compile(EMAIL_PATTERN)


# A field that is one address as a whole, whatever it looks like ("?@example.com" too).
EMAIL_FIELD = "email"


def addresses(name: str, value: str) -> list[str]:
    return [value.strip()] if name == EMAIL_FIELD else EMAIL.findall(value)


def unknown_emails(arguments: dict, fields: tuple[str, ...], seen: str) -> list[str]:
    """The addresses in an action's texts (`fields`) that appear nowhere in `seen`, what the
    user wrote and the tools returned: ones the model made up."""
    seen = seen.lower()

    return [
        address
        for name in fields
        if isinstance(arguments.get(name), str)
        for address in addresses(name, arguments[name])
        if address.lower() not in seen
    ]
