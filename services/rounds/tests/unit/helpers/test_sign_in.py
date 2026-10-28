import asyncio

import pytest

from rounds.helpers.sign_in import sign_in_block, with_sign_in


def events(chunks: list[str]) -> list[dict]:
    async def stream():
        for chunk in chunks:
            yield chunk

    async def collect():
        return [event async for event in with_sign_in(stream())]

    return asyncio.run(collect())


@pytest.mark.parametrize(
    "chunks, provider",
    [
        (["[[sign_in:google]] Sign in", " below."], "google"),
        (["[[sig", "n_in:git", "hub]]", " Sign in below."], "github"),
        ([" [[sign_in]]Sign in below."], None),
    ],
)
def test_the_marker_becomes_a_sign_in_card_and_the_rest_streams(chunks, provider):
    found = events(chunks)

    assert found[0] == {"block": sign_in_block(provider)}
    assert "".join(event.get("delta", "") for event in found).strip() == "Sign in below."


@pytest.mark.parametrize(
    "chunks",
    [
        ["Credits cost ", "$1–3 per candidate."],
        ["[", "[Link]] to pricing"],
        ["[[sign_in:twitter]] no"],
    ],
)
def test_other_replies_stream_unchanged(chunks):
    found = events(chunks)

    assert all("block" not in event for event in found)
    assert "".join(event["delta"] for event in found) == "".join(chunks)


def test_a_reply_that_is_only_the_marker_is_only_the_card():
    assert events(["[[sign_in:linkedin]]"]) == [{"block": sign_in_block("linkedin")}]
