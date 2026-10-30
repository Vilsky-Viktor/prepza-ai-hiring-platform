from datetime import datetime
from email.utils import format_datetime
from urllib.parse import urlencode

from fastapi import Request, Response

from api.config import settings
from api.constants.api import API_BASE, CANDIDATE_LINK, CHANGELOG_LINK, INVITE_LINK
from api.schemas.public import Candidate, Interview, Note, Signals


def interview_of(found: dict) -> Interview:
    """Companies' interview, as the API shows it."""
    return Interview(
        id=found["id"],
        title=found["title"],
        status=found["status"],
        ready=found["set_id"] is not None,
        pass_mark=found["pass_mark"],
        candidate_count=found["candidate_count"],
        created_at=found["created_at"],
        updated_at=found.get("updated_at"),
    )


def candidate_of(found: dict, company_id, interview_id, site: str) -> Candidate:
    """Companies' candidate, as the API shows it, with a link to their results in prepza and,
    until they finish, their invite link."""
    token = found.get("invite_token")

    return Candidate(
        id=found["id"],
        interview_id=interview_id,
        email=found["email"],
        name=found.get("name"),
        status=found["status"],
        progress=found["progress"],
        grade=found["grade"],
        passed=found["passed"],
        signals=Signals(
            tab_leaves=found["tab_leaves"],
            copies=found["copies"],
            fast_answers=found["fast_answers"],
            answer_patterns=(
                None
                if found.get("answer_signals") is None
                else [signal["kind"] for signal in found["answer_signals"]]
            ),
        ),
        flagged=found.get("flagged", False),
        extra_time=found.get("extra_time", 0),
        mode="voice" if found.get("voice") else "click",
        sections=found.get("sections"),
        results_url=CANDIDATE_LINK.format(
            site=site, company_id=company_id, interview_id=interview_id, invite_id=found["id"]
        ),
        invite_url=INVITE_LINK.format(site=site, token=token) if token else None,
        created_at=found["created_at"],
        updated_at=found.get("updated_at"),
        started_at=found.get("started_at"),
        finished_at=found.get("finished_at"),
    )


def note_of(found: dict) -> Note:
    """Companies' note, as the API shows it: its author by name only, null for a former member."""
    return Note(
        id=found["id"],
        text=found["text"],
        author=found["author"]["name"],
        pinned=found["pinned"],
        created_at=found["created_at"],
        edited_at=found["edited_at"],
    )


def next_link(site: str, path: str, offset: int, limit: int, found: list, syncing: bool):
    """A list's `Link` header when there may be a next page (this one is full; the next can come
    back empty): the next page's address, by `offset`, or when syncing (`updated_since`), from
    the last item's `updated_at` and `id`. None on the last page."""
    if len(found) < limit:
        return None

    if syncing:
        last = found[-1]
        query = {"limit": limit, "updated_since": last.updated_at.isoformat(), "after": last.id}
    else:
        query = {"offset": offset + limit, "limit": limit}

    return f'<{API_BASE.format(site=site)}{path}?{urlencode(query)}>; rel="next"'


def link_next(
    request: Request, response: Response, offset: int, limit: int, listed: list, syncing: bool
) -> None:
    """Puts the next page's address in the list's `Link` header, when there may be one."""
    link = next_link(settings.site_url, request.url.path, offset, limit, listed, syncing)

    if link:
        response.headers["Link"] = link


def deprecation_headers(deprecated_at: datetime, sunset_at: datetime, site: str) -> dict:
    """What a retired route answers with until it's gone: when it was deprecated (RFC 9745), when
    it stops working (RFC 8594) and the changelog that says what to use instead."""
    return {
        "Deprecation": f"@{int(deprecated_at.timestamp())}",
        "Sunset": format_datetime(sunset_at, usegmt=True),
        "Link": f'<{CHANGELOG_LINK.format(site=site)}>; rel="deprecation"; type="text/html"',
    }
