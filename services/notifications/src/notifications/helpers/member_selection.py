# Who gets which activity digest and reminders, from what other services answered. Rows are
# (the template's line, the values that fill it, the page it links to).
from datetime import datetime

from notifications.constants.member_emails import (
    AWAITING_REVIEW,
    INTERVIEW_LINK,
    REVIEW_WAITING_DAYS,
    TOP_UP_LINK,
)
from notifications.constants.unsubscribe import DIGEST_KINDS


def digest_sections(
    user_id: str, preferences: dict, companies: list[dict], activity: list, site: str
) -> list:
    """The digest's lists for one user: each company they're a member of that had activity of a
    kind they get, by name, with a line per kind and page (an interview, the ATS tab) saying how
    many. None of them, nothing to send."""
    kinds = [kind for kind in DIGEST_KINDS if preferences.get(kind)]
    sections = []

    for company in sorted(companies, key=lambda found: found["name"].lower()):
        if all(member["user_id"] != user_id for member in company["members"]):
            continue

        lines = {}

        for item in activity:
            if item.recipient_id != company["id"] or item.kind not in kinds:
                continue

            line = lines.setdefault(
                (item.kind, item.link), {"title": item.data.get("title") or "", "count": 0}
            )

            # An ATS's line names that ATS.
            if item.data.get("ats"):
                line["ats"] = item.data["ats"]

            line["count"] += item.data.get("count", 1)

        rows = [
            (kind, values, site + link)
            for (kind, link), values in sorted(
                lines.items(), key=lambda pair: (kinds.index(pair[0][0]), pair[1]["title"].lower())
            )
        ]

        if rows:
            sections.append((company["name"], rows))

    return sections


def editors(companies: list[dict]) -> dict[str, list[str]]:
    """Each company's owners and admins, by its id: who can act on a reminder."""
    return {
        company["id"]: [member["user_id"] for member in company["members"] if member["editor"]]
        for company in companies
    }


def low_credit_rows(low: list[dict], companies: list[dict], site: str) -> dict[str, list]:
    """Each owner's or admin's companies running low on credits, by user."""
    names = {company["id"]: company["name"] for company in companies}
    can_act = editors(companies)
    by_user = {}

    for wallet in low:
        company_id = wallet["company_id"]

        for user_id in can_act.get(company_id, []):
            values = {"company": names[company_id], "available": wallet["available"]}
            by_user.setdefault(user_id, []).append(
                (company_id, ("company", values, site + TOP_UP_LINK))
            )

    return by_user


def interview_rows(
    interviews: list[dict], users: dict[str, list[str]], companies: list[dict], site: str, values
) -> dict[str, list]:
    """A line for each interview, to each of `users` (by the interview's id), filled by
    `values(interview, company name)`."""
    names = {company["id"]: company["name"] for company in companies}
    by_user = {}

    for interview in interviews:
        company_id = interview["company_id"]

        if company_id not in names:
            continue

        link = site + INTERVIEW_LINK.format(company_id=company_id, interview_id=interview["id"])
        row = ("interview", values(interview, names[company_id]), link)

        for user_id in users.get(interview["id"], []):
            by_user.setdefault(user_id, []).append((interview["id"], row))

    return by_user


def awaiting_review(
    being_generated: list[dict], statuses: list[dict], now: datetime, companies: list[dict]
) -> tuple[list[dict], dict[str, list[str]]]:
    """The interviews whose topics have waited for a review for REVIEW_WAITING_DAYS or more,
    each with how many whole days ("days"), and for each who started it, while they're still
    an owner or admin of its company."""
    waiting = {
        found["id"]: (found["owner_uid"], (now - datetime.fromisoformat(found["updated_at"])).days)
        for found in statuses
        if found["status"] == AWAITING_REVIEW
    }
    can_act = editors(companies)
    interviews = [
        {**interview, "days": waiting[interview["generation_id"]][1]}
        for interview in being_generated
        if interview["generation_id"] in waiting
        and waiting[interview["generation_id"]][1] >= REVIEW_WAITING_DAYS
        and waiting[interview["generation_id"]][0] in can_act.get(interview["company_id"], [])
    ]

    return interviews, {
        interview["id"]: [waiting[interview["generation_id"]][0]] for interview in interviews
    }


def next_companies(
    low: list[str], waiting: list[str], after: str, limit: int
) -> tuple[list[str], str]:
    """The reminders' next page of companies after `after`, in order, and where the page after
    it starts: those running low on credits (`low`, all of them) and those with interviews
    waiting (`waiting`, a page of at most `limit` from companies). While `waiting` is a full
    page, nothing past its last id is taken: the next page reads on from there."""
    cut = waiting[-1] if len(waiting) >= limit else None
    more = [
        company_id for company_id in low if company_id > after and (not cut or company_id <= cut)
    ]
    page = sorted({*waiting, *more})[:limit]

    return page, page[-1] if page else after
