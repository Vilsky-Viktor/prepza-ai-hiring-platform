import asyncio
from types import SimpleNamespace

from app.services import digest, member_pages, member_sends
from tests.unit.member_world import NOW, finished, person

ACME = {"id": "c1", "name": "Acme", "members": [{"user_id": "ann", "editor": True}]}
ZETA = {
    "id": "c2",
    "name": "Zeta",
    "members": [{"user_id": "ann", "editor": False}, {"user_id": "bo", "editor": True}],
}


def test_the_digest_goes_a_page_of_companies_at_a_time_each_member_once_with_all_theirs(
    world, monkeypatch
):
    """Ann, found on the first page, gets one digest covering both her companies; Bo, only in
    the second, gets his from the second page."""
    monkeypatch.setattr(digest, "MEMBER_PAGE", 1)
    world.update(
        companies=[ACME, ZETA],
        activity=[finished("c1"), finished("c2", "/i2")],
        people=[person("ann"), person("bo")],
    )

    sent = asyncio.run(digest.send_digests(NOW))
    emails = {email.to: email for email, _ in world["sent"]}

    assert sent == 2
    assert sorted(emails) == ["ann@example.com", "bo@example.com"]
    assert "Acme" in emails["ann@example.com"].html and "Zeta" in emails["ann@example.com"].html
    assert "Acme" not in emails["bo@example.com"].html
    # Each page read after the last one's last company, and the day's cursor moved on.
    assert world["pages"] == ["", "c1", "c2"]
    assert world["cursors"] == {("digest", NOW.date()): "c2"}


def test_a_run_out_of_time_leaves_its_page_to_the_next_which_skips_who_got_theirs(
    world, monkeypatch
):
    clock = SimpleNamespace(now=0.0)
    ticking = SimpleNamespace(monotonic=lambda: clock.now)
    monkeypatch.setattr(member_sends, "time", ticking)
    monkeypatch.setattr(member_pages, "time", ticking)
    send = member_sends.delivery.send

    async def slow(email, key):
        await send(email, key)

        # The first email takes its run past the deadline.
        if len(world["sent"]) == 1:
            clock.now = 100.0

    monkeypatch.setattr(member_sends.delivery, "send", slow)

    first = asyncio.run(digest.send_digests(NOW))
    cursor_after_first = dict(world["cursors"])
    clock.now = 0.0
    second = asyncio.run(digest.send_digests(NOW))

    assert (first, second) == (1, 1)
    assert sorted(email.to for email, _ in world["sent"]) == ["ann@example.com", "vic@example.com"]
    assert cursor_after_first == {}
    assert world["cursors"] == {("digest", NOW.date()): "c1"}
