# Whom a bulk send goes to, a page at a time. An audience is one or more sources of user ids, read
# one after the other, each a page after its last id; the send's cursor (bulk_sends.
# prepared_after) is "<source>:<last id>". Someone in several sources is saved once
# (bulk_recipients is unique per send and user), so they get one email.
import uuid

from prepza_common.constants import GUEST_UID_PREFIX
from prepza_common.paging import ID_PAGE_SIZE

from app.constants.bulk import LEGAL_KINDS, OPTIONAL_KINDS, BulkKind
from app.constants.campaigns import AudienceGroup
from app.integrations import companies, library, rounds
from app.models.audience import Audience, Source
from app.schemas.campaigns import AudienceIn
from app.storage import campaigns


def without_guests(user_ids: list[str]) -> list[str]:
    """Never a company's guest candidate."""
    return [user_id for user_id in user_ids if not user_id.startswith(GUEST_UID_PREFIX)]


def companies_source(company_ids: list[uuid.UUID], editors_only: bool) -> Source:
    """The members of some companies (an important notice about an incident that affects them),
    read at once: a few companies' members, in order."""

    async def read(after: str) -> list[str]:
        found = await companies.members([str(company_id) for company_id in company_ids])
        ids = {
            member["user_id"]
            for company in found
            for member in company["members"]
            if member["editor"] or not editors_only
        }

        return sorted(user_id for user_id in ids if user_id > after)[:ID_PAGE_SIZE]

    return read


def group_source(group: AudienceGroup, chosen: AudienceIn) -> Source:
    if group == AudienceGroup.MEMBERS and chosen.company_ids:
        return companies_source(chosen.company_ids, chosen.editors_only)

    if group == AudienceGroup.MEMBERS:
        return lambda after: companies.member_ids(after, chosen.editors_only)

    return lambda after: rounds.user_ids(group, after)


def campaign_audience(chosen: AudienceIn) -> Audience:
    """A campaign's audience: everyone (every account for an important notice, the users with
    the setting on for the others), or the people in its groups, with the setting on for an
    optional kind."""
    setting = chosen.kind if chosen.kind in OPTIONAL_KINDS else None

    if not chosen.groups:
        return Audience([lambda after: library.user_ids(after, setting)])

    groups = [group for group in AudienceGroup if group in chosen.groups]

    return Audience([group_source(group, chosen) for group in groups], setting)


async def audience_of(kind: str, about: str) -> Audience:
    """A send's audience: every account for the terms and the privacy policy, every company's
    owner and admin for the DPA, and a campaign's own; nobody for a campaign that's gone."""
    if kind == BulkKind.LEGAL_DPA:
        return Audience([lambda after: companies.member_ids(after, True)])

    if kind in LEGAL_KINDS:
        return Audience([library.user_ids])

    found = await campaigns.get(uuid.UUID(about))

    if found is None:
        return Audience([])

    campaign = found[0]

    return campaign_audience(
        AudienceIn(
            kind=campaign.kind,
            groups=campaign.groups,
            editors_only=campaign.editors_only,
            company_ids=campaign.company_ids,
        )
    )


async def page_of(audience: Audience, cursor: str) -> tuple[list[str], str, bool]:
    """The page of the audience after `cursor` (never a guest), the cursor after it, and whether
    the audience has ended."""
    index, _, after = cursor.partition(":") if cursor else ("0", "", "")
    index = int(index)

    if index >= len(audience.sources):
        return [], cursor, True

    page = await audience.sources[index](after)
    user_ids = without_guests(page)

    if audience.setting and user_ids:
        user_ids = await library.with_setting(user_ids, audience.setting)

    if len(page) >= ID_PAGE_SIZE:
        return user_ids, f"{index}:{page[-1]}", False

    if index + 1 < len(audience.sources):
        return user_ids, f"{index + 1}:", False

    return user_ids, f"{index}:{page[-1] if page else after}", True


async def everyone(audience: Audience) -> list[str]:
    """Every user of the audience, once each."""
    found: dict[str, None] = {}
    cursor = ""

    while True:
        page, cursor, done = await page_of(audience, cursor)
        found.update(dict.fromkeys(page))

        if done:
            return list(found)
