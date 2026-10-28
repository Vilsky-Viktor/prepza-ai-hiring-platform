from collections.abc import AsyncIterator

from prepza_common.ai.secrets_check import SECRET_REMOVED
from prepza_common.http.sse import sse_event
from prepza_common.i18n.i18n import translate

from rounds.constants.help import SIGN_IN_MARKER, SIGN_IN_PREFIX


def sign_in_block(provider: str | None) -> dict:
    """The panel's sign-in card, with the way the visitor asked for first."""
    return {"kind": "sign_in", "items": [], "links": [], "provider": provider}


async def with_sign_in(chunks: AsyncIterator[str]) -> AsyncIterator[dict]:
    """A reply's events: {"delta"} for its text, and {"block"} with a sign-in card in place of
    the marker a reply to "sign me in" starts with. The start is held back only until it can't
    be the marker any more."""
    held = ""
    decided = False

    async for chunk in chunks:
        if decided:
            yield {"delta": chunk}

            continue

        held += chunk
        start = held.lstrip()

        # Still possibly the marker: wait for more.
        if SIGN_IN_PREFIX.startswith(start) or (
            start.startswith(SIGN_IN_PREFIX) and "]]" not in start
        ):
            continue

        decided = True

        for event in split(held):
            yield event

    if not decided and held:
        for event in split(held):
            yield event


def split(text: str) -> list[dict]:
    found = SIGN_IN_MARKER.match(text)

    if found is None:
        return [{"delta": text}]

    rest = text[found.end() :]
    events = [{"block": sign_in_block(found.group(1))}]

    return [*events, {"delta": rest}] if rest else events


async def secret_reply(language: str) -> AsyncIterator[str]:
    """The fixed answer to a message with a secret: the panel removes it, then reads why."""
    yield sse_event({"removed": True})
    yield sse_event({"delta": translate(SECRET_REMOVED, language)})
    yield sse_event({"done": True})
