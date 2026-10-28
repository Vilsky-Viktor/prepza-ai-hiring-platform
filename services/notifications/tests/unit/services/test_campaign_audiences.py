import asyncio
import uuid

import pytest
from fastapi import HTTPException

from notifications.config import settings
from notifications.constants.campaigns import (
    COMPANIES_ONLY_NOTICES,
    OWNERS_NEED_COMPANIES,
)
from notifications.helpers.campaign_emails import campaign_email
from notifications.helpers.senders import sender
from notifications.helpers.unsubscribe import address_hash
from notifications.models.audience import Audience
from notifications.repositories import suppressed
from notifications.schemas.campaigns import AudienceIn
from notifications.services import audiences, bulk, campaign_sends, campaigns

COMPANY = str(uuid.uuid4())
TEXTS = {"en": {"subject": "Planned downtime", "text": "Down on Sunday.", "button": None}}


def person(user_id, **preferences):
    return {
        "user_id": user_id,
        "email": f"{user_id}@example.com",
        "language": "en",
        "preferences": preferences,
    }


def source(ids, asked):
    """A source of these ids, read `size` a page, recording what it was asked."""

    async def read(after):
        asked.append(after)

        return [user_id for user_id in sorted(ids) if user_id > after][:2]

    return read


@pytest.fixture
def paged(monkeypatch):
    """Pages of two ids; the setting filter keeps the ids in `on`."""
    monkeypatch.setattr(audiences, "ID_PAGE_SIZE", 2)
    filtered = []

    async def with_setting(user_ids, setting):
        filtered.append((list(user_ids), setting))

        return [user_id for user_id in user_ids if user_id in {"a", "c"}]

    monkeypatch.setattr(audiences.library, "with_setting", with_setting)

    return filtered


def test_sources_are_read_one_after_the_other_a_page_at_a_time_without_guests(paged):
    first, second = [], []
    audience = Audience([source(["a", "b", "c"], first), source(["b", "guest-x"], second)])

    async def every_page():
        pages, cursor = [], ""

        while True:
            page, cursor, done = await audiences.page_of(audience, cursor)
            pages.append((page, cursor))

            if done:
                return pages

    pages = asyncio.run(every_page())

    # The second source's page is full, so it's read once more, and comes back empty.
    assert pages == [
        (["a", "b"], "0:b"),
        (["c"], "1:"),
        (["b"], "1:guest-x"),
        ([], "1:guest-x"),
    ]
    assert (first, second) == (["", "b"], ["", "guest-x"])
    # Without a setting to have on (an important notice), nothing is filtered.
    assert paged == []


def test_an_optional_campaign_to_groups_keeps_only_who_has_its_setting_on(paged):
    audience = Audience([source(["a", "b", "guest-x"], [])], setting="updates")

    page, _, _ = asyncio.run(audiences.page_of(audience, ""))

    assert page == ["a"]
    assert paged == [(["a", "b"], "updates")]


@pytest.mark.parametrize(
    ("chosen", "reads"),
    [
        # Everyone: every account for a notice, those with the setting on otherwise.
        (AudienceIn(kind="notices"), [("library", None)]),
        (AudienceIn(kind="updates"), [("library", "updates")]),
        # Groups in their own order, whatever order they were ticked in.
        (
            AudienceIn(kind="notices", groups=["learners", "members"], editors_only=True),
            [("members", True), ("rounds", "learners")],
        ),
        (AudienceIn(kind="promotions", groups=["candidates"]), [("rounds", "candidates")]),
    ],
)
def test_a_campaigns_audience_reads_what_its_choice_names(monkeypatch, chosen, reads):
    asked = []

    async def user_ids(after, setting=None):
        asked.append(("library", setting))

        return []

    async def member_ids(after, editors_only):
        asked.append(("members", editors_only))

        return []

    async def rounds_ids(group, after):
        asked.append(("rounds", group))

        return []

    monkeypatch.setattr(audiences.library, "user_ids", user_ids)
    monkeypatch.setattr(audiences.companies, "member_ids", member_ids)
    monkeypatch.setattr(audiences.rounds, "user_ids", rounds_ids)

    asyncio.run(audiences.everyone(audiences.campaign_audience(chosen)))

    assert asked == reads


def test_a_notice_to_some_companies_goes_to_their_members_or_owners_and_admins(monkeypatch):
    async def members(company_ids):
        assert company_ids == [COMPANY]
        found = [{"user_id": "vic", "editor": False}, {"user_id": "ann", "editor": True}]

        return [{"id": COMPANY, "name": "Acme", "members": found}]

    monkeypatch.setattr(audiences.companies, "members", members)
    every = AudienceIn(kind="notices", groups=["members"], company_ids=[COMPANY])
    editors = every.model_copy(update={"editors_only": True})

    assert asyncio.run(audiences.everyone(audiences.campaign_audience(every))) == ["ann", "vic"]
    assert asyncio.run(audiences.everyone(audiences.campaign_audience(editors))) == ["ann"]


@pytest.mark.parametrize(
    ("chosen", "error"),
    [
        (AudienceIn(kind="notices", editors_only=True), OWNERS_NEED_COMPANIES),
        (
            AudienceIn(kind="updates", groups=["members"], company_ids=[COMPANY]),
            COMPANIES_ONLY_NOTICES,
        ),
        (
            AudienceIn(kind="notices", groups=["learners"], company_ids=[COMPANY]),
            COMPANIES_ONLY_NOTICES,
        ),
    ],
)
def test_an_audience_that_cant_be_chosen_is_refused(chosen, error):
    with pytest.raises(HTTPException) as refused:
        campaigns.checked_audience(chosen)

    assert (refused.value.status_code, refused.value.detail) == (422, error)


def test_each_group_and_company_is_kept_once():
    chosen = AudienceIn(
        kind="notices", groups=["members", "members"], company_ids=[COMPANY, COMPANY]
    )

    checked = campaigns.checked_audience(chosen)

    assert (checked.groups, [str(one) for one in checked.company_ids]) == (["members"], [COMPANY])


def test_a_notice_is_a_service_email_from_the_service_sender_with_nothing_to_unsubscribe():
    email = campaign_email(
        "notices", person("ann"), TEXTS, None, "https://prepza.com", "secret", "s-1"
    )

    assert not email.optional and sender(email) == settings.mail_from
    assert "List-Unsubscribe" not in email.headers and "/unsubscribe" not in email.text
    assert email.tags == {"kind": "notices", "id": "ann", "send": "s-1"}
    assert email.subject == "Planned downtime"


def test_a_notice_reaches_everyone_whatever_their_settings_but_never_a_suppressed_address(
    monkeypatch,
):
    async def member_ids(after, editors_only):
        return ["ann", "bob"]

    async def rounds_ids(group, after):
        return ["bob", "cat"]

    async def recipients(ids):
        assert ids == ["ann", "bob", "cat"]

        return [person(user_id) for user_id in ids]

    async def among(hashes):
        return {address_hash("cat@example.com")} & set(hashes)

    monkeypatch.setattr(audiences.companies, "member_ids", member_ids)
    monkeypatch.setattr(audiences.rounds, "user_ids", rounds_ids)
    monkeypatch.setattr(campaign_sends.library, "recipients", recipients)
    monkeypatch.setattr(suppressed, "among", among)
    chosen = AudienceIn(kind="notices", groups=["members", "candidates"])

    # Bob, a member and a candidate, counts once; Cat's address is suppressed.
    assert asyncio.run(campaign_sends.reachable(chosen)) == 2


def test_a_notice_skips_only_gone_and_suppressed_people_never_for_a_setting_off():
    hashes = {address_hash("cat@example.com")}

    assert bulk.skip_reason("notices", person("ann", updates=False), hashes) is None
    assert bulk.skip_reason("notices", person("cat"), hashes) == "suppressed"
    assert bulk.skip_reason("updates", person("ann", updates=False), hashes) == "unsubscribed"
