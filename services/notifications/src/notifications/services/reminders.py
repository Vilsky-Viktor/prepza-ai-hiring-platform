from datetime import datetime, timedelta

from notifications.config import settings
from notifications.constants.member_emails import (
    MEMBER_PAGE,
    NO_CANDIDATES_DAYS,
    NO_CANDIDATES_WINDOW_DAYS,
    REMINDER_DAYS,
    REMINDERS_JOB,
    REVIEW_STARTED_DAYS,
    REVIEW_WAITING_DAYS,
    MemberEmail,
)
from notifications.helpers.member_emails import reminder_email
from notifications.helpers.member_selection import (
    awaiting_review,
    editors,
    interview_rows,
    low_credit_rows,
    next_companies,
)
from notifications.integrations import accounts, billing, companies, generation
from notifications.services.member_pages import each_page, their_companies
from notifications.services.member_sends import deadline, send_once


async def send_reminders(now: datetime) -> int:
    """Reminders to owners and admins who get them: companies running low on credits,
    interviews nobody was invited to NO_CANDIDATES_DAYS after they were ready, and, to whoever
    started one, topics waiting for a review for REVIEW_WAITING_DAYS. Each kind at most once in
    REMINDER_DAYS to a user, and each interview named once. A page of those companies at a time
    (services/member_pages.py): each page's owners and admins get theirs, every company of
    theirs included. Returns how many were sent."""
    stop = deadline()
    ready = (
        now - timedelta(days=NO_CANDIDATES_WINDOW_DAYS),
        now - timedelta(days=NO_CANDIDATES_DAYS),
    )
    started = (now - timedelta(days=REVIEW_STARTED_DAYS), now - timedelta(days=REVIEW_WAITING_DAYS))
    low = await billing.low_companies()
    low_ids = sorted({wallet["company_id"] for wallet in low})

    async def read_page(after: str) -> tuple[list[str], str]:
        waiting = await companies.waiting_company_ids(ready, started, after, MEMBER_PAGE)

        return next_companies(low_ids, waiting, after, MEMBER_PAGE)

    async def send_page(company_ids: list[str]) -> int:
        found = await companies.members(company_ids)
        user_ids = sorted({user_id for ids in editors(found).values() for user_id in ids})
        theirs = await their_companies(user_ids)
        rows = await reminder_rows(now, ready, started, low, theirs)
        recipients = [
            recipient
            for recipient in await accounts.recipients(user_ids)
            if recipient["preferences"]["reminders"]
        ]
        sent = 0

        for kind, by_user in rows.items():
            jobs = [
                (
                    recipient["user_id"],
                    tracked(kind, by_user[recipient["user_id"]]),
                    email_for(kind, recipient, by_user[recipient["user_id"]]),
                )
                for recipient in recipients
                if recipient["user_id"] in by_user
            ]
            sent += await send_once(kind, now.date(), REMINDER_DAYS, jobs, stop)

        return sent

    return await each_page(REMINDERS_JOB, now.date(), read_page, send_page, stop)


async def reminder_rows(now, ready, started, low: list[dict], company_ids: list[str]) -> dict:
    """Each kind's lines by user, for those companies."""
    waiting = await companies.waiting_interviews(ready, started, company_ids)
    idle, generating = waiting["without_candidates"], waiting["being_generated"]
    statuses = await generation.statuses([found["generation_id"] for found in generating])
    found = await companies.members(company_ids)
    site = settings.site_url.rstrip("/")
    can_act = editors(found)
    reviews, starters = awaiting_review(generating, statuses, now, found)
    theirs = set(company_ids)

    return {
        MemberEmail.LOW_CREDITS: low_credit_rows(
            [wallet for wallet in low if wallet["company_id"] in theirs], found, site
        ),
        MemberEmail.NO_CANDIDATES: interview_rows(
            idle,
            {interview["id"]: can_act.get(interview["company_id"], []) for interview in idle},
            found,
            site,
            lambda interview, company: {"title": interview["title"] or "", "company": company},
        ),
        MemberEmail.REVIEW_WAITING: interview_rows(
            reviews,
            starters,
            found,
            site,
            lambda interview, company: {"days": interview["days"], "company": company},
        ),
    }


def tracked(kind: MemberEmail, items: list) -> list[str]:
    """What a reminder names that it mustn't name again: interviews. Credits are reminded
    about again each REMINDER_DAYS while they stay low."""
    if kind == MemberEmail.LOW_CREDITS:
        return []

    return [item_id for item_id, _ in items]


def email_for(kind: MemberEmail, recipient: dict, items: list):
    """Builds the reminder from the items not named before (all of them for credits)."""

    def build(new: list[str]):
        rows = [row for item_id, row in items if not new or item_id in new]

        return reminder_email(kind, recipient, rows, settings.site_url, settings.email_link_secret)

    return build
