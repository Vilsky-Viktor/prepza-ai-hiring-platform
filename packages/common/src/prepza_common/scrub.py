"""Personal data and secrets taken out of what leaves us for a processor (Sentry, Langfuse)."""

import re

from prepza_common.constants import EMAIL_PATTERN
from prepza_common.scrub_patterns import (
    PERSON_FIELD_ENDINGS,
    PERSON_FIELD_PATTERN,
    QUERY_FIELDS,
    REDACTED_EMAIL,
    REDACTED_PERSON,
    URL_PATTERN,
    URL_SCRUBBED,
)


def scrub(value):
    """Replaces every email address, however deep it sits, and cuts every URL to its scheme and
    host: outgoing calls' URLs (web hooks, Slack) and invite links are secrets. Fields that hold
    a query alone are dropped."""
    if isinstance(value, str):
        return re.sub(EMAIL_PATTERN, REDACTED_EMAIL, re.sub(URL_PATTERN, URL_SCRUBBED, value))

    if isinstance(value, dict):
        return {key: scrub(item) for key, item in value.items() if key not in QUERY_FIELDS}

    if isinstance(value, list | tuple):
        return [scrub(item) for item in value]

    return value


def scrub_people(value, hidden: tuple[str, ...] = ()):
    """`scrub`, and also people's names: the value of a field named `name` or `email` or ending so (`candidate_name`), in data or in JSON
    text (a tool's result), and each of `hidden` (a name the caller knows is in the text). Any
    other object is scrubbed as its JSON form or its text."""
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")

    if isinstance(value, str):
        value = re.sub(PERSON_FIELD_PATTERN, rf'\1"{REDACTED_PERSON}"', scrub(value))

        for word in hidden:
            value = re.sub(rf"\b{re.escape(word)}\b", REDACTED_PERSON, value)

        return value

    if isinstance(value, dict):
        return {
            key: REDACTED_PERSON
            if isinstance(key, str) and key.endswith(PERSON_FIELD_ENDINGS) and isinstance(item, str)
            else scrub_people(item, hidden)
            for key, item in value.items()
            if key not in QUERY_FIELDS
        }

    if isinstance(value, list | tuple):
        return [scrub_people(item, hidden) for item in value]

    if value is None or isinstance(value, bool | int | float):
        return value

    return scrub_people(str(value), hidden)
