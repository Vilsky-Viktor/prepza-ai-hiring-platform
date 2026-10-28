from datetime import datetime, timedelta

from notifications.config import settings
from notifications.constants.member_emails import (
    DIGEST_HOUR,
    DIGEST_HOURS,
    MEMBER_PAGE,
    MemberEmail,
)
from notifications.constants.unsubscribe import DIGEST_KINDS
from notifications.core.db import Session
from notifications.helpers.member_emails import digest_email
from notifications.helpers.member_selection import digest_sections
from notifications.integrations import companies, library
from notifications.repositories import digest_activity
from notifications.services.member_pages import each_page, their_companies
from notifications.services.member_sends import deadline, send_once


async def send_digests(now: datetime) -> int:
    """The activity digest: one email a day to each member of a company that had activity of a
    kind they get, in the 24 hours before the day's DIGEST_HOUR (the same for every run that day,
    the catch-up hour's too), covering all their companies. A page of active companies at a
    time (services/member_pages.py): each page's members get theirs, every company of theirs
    included. Returns how many were sent."""
    until = now.replace(hour=DIGEST_HOUR, minute=0, second=0, microsecond=0)
    since = until - timedelta(hours=DIGEST_HOURS)
    stop = deadline()

    async def read_page(after: str) -> tuple[list[str], str]:
        async with Session() as session:
            found = await digest_activity.active_companies(
                session, DIGEST_KINDS, since, until, after, MEMBER_PAGE
            )

        return found, found[-1] if found else after

    async def send_page(company_ids: list[str]) -> int:
        found = await companies.members(company_ids)
        user_ids = sorted({member["user_id"] for company in found for member in company["members"]})
        theirs = await their_companies(user_ids)
        everywhere = await companies.members(theirs)

        async with Session() as session:
            activity = await digest_activity.companies_activity(
                session, DIGEST_KINDS, since, until, theirs
            )

        site = settings.site_url.rstrip("/")
        jobs = []

        for recipient in await library.recipients(user_ids):
            sections = digest_sections(
                recipient["user_id"], recipient["preferences"], everywhere, activity, site
            )

            if sections:
                jobs.append((recipient["user_id"], [], email_for(recipient, sections)))

        return await send_once(MemberEmail.DIGEST, until.date(), 1, jobs, stop)

    return await each_page(MemberEmail.DIGEST, until.date(), read_page, send_page, stop)


def email_for(recipient: dict, sections: list):
    return lambda new: digest_email(
        recipient, sections, settings.site_url, settings.email_link_secret
    )
