import asyncio

import pytest

from notifications.constants.member_emails import REMINDERS_JOB
from notifications.helpers.member_selection import next_companies
from notifications.services import reminders
from tests.unit.member_world import NOW, person

ACME = {"id": "c1", "name": "Acme", "members": [{"user_id": "ann", "editor": True}]}
ZETA = {
    "id": "c2",
    "name": "Zeta",
    "members": [{"user_id": "ann", "editor": True}, {"user_id": "bo", "editor": True}],
}


@pytest.mark.parametrize(
    "low, waiting, after, page, next_after",
    [
        # Waiting's page is full: nothing past its last id, the next page reads on from there.
        (["c1", "c3"], ["c2", "c4"], "", ["c1", "c2"], "c2"),
        # Waiting's page is short: every company left that runs low comes too, up to a page.
        (["c3", "c5"], ["c4"], "c2", ["c3", "c4"], "c4"),
        (["c1"], [], "c1", [], "c1"),
        # A company both waiting and low comes once.
        (["c2"], ["c2"], "", ["c2"], "c2"),
    ],
)
def test_the_next_page_of_companies_takes_both_in_order_without_skipping(
    low, waiting, after, page, next_after
):
    assert next_companies(low, waiting, after, 2) == (page, next_after)


def test_reminders_go_a_page_of_companies_at_a_time_each_owner_once_with_all_theirs(
    world, monkeypatch
):
    """Ann, found on the first page, gets one reminder naming both her companies running low;
    Bo, only in the second, gets his from the second page."""
    monkeypatch.setattr(reminders, "MEMBER_PAGE", 1)
    world.update(
        companies=[ACME, ZETA],
        low=[{"company_id": "c1", "available": 100}, {"company_id": "c2", "available": 50}],
        people=[person("ann"), person("bo")],
    )

    asyncio.run(reminders.send_reminders(NOW))
    low_credits = {
        email.to: email for email, _ in world["sent"] if "credits" in email.subject.lower()
    }

    assert sorted(low_credits) == ["ann@example.com", "bo@example.com"]
    assert "Acme" in low_credits["ann@example.com"].html
    assert "Zeta" in low_credits["ann@example.com"].html
    assert "Acme" not in low_credits["bo@example.com"].html
    # Waiting companies read a page after the last page's last company; the cursor moved on.
    assert world["waiting_pages"] == ["", "c1", "c2"]
    assert world["cursors"] == {(REMINDERS_JOB, NOW.date()): "c2"}
