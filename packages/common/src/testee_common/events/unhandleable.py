"""Events no retry can handle. A consumer's failure answers Pub/Sub with an error, so the event
comes again; an event that lacks the data its handler needs, carries a malformed value, or names
something that doesn't exist would fail the same way on every redelivery (50 times over hours
in production, without end on the local emulator). Such an event is logged as an error (Sentry
reports it) and acknowledged; any other failure (a database, Redis or service outage, a
timeout, an overload) still raises, and Pub/Sub retries it with backoff."""

import logging
from collections.abc import Awaitable

import httpx
from sqlalchemy.exc import DataError, IntegrityError, NoResultFound
from starlette.exceptions import HTTPException
from testee_common.config.event_constants import FINAL_STATUSES

logger = logging.getLogger(__name__)


class BadEvent(Exception):
    """Raised by a handler for an event it can never handle: data it needs is missing, or the
    ids it carries match nothing."""


# Failures of the event itself: data missing (KeyError) or of the wrong kind (TypeError,
# ValueError, which pydantic's validation errors are too), values the database refuses (a
# malformed value, an id no row has) or a row the event names that isn't there.
FINAL_ERRORS = (BadEvent, KeyError, TypeError, ValueError, DataError, IntegrityError, NoResultFound)


def final(error: Exception) -> bool:
    """Whether a retry would fail the same way: an error of the event itself, or an answer
    (another service's, or a service's own refusal it raises for its routes) that says so."""
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code in FINAL_STATUSES

    if isinstance(error, HTTPException):
        return error.status_code in FINAL_STATUSES

    return isinstance(error, FINAL_ERRORS)


async def handle_or_drop(handling: Awaitable[None], event_type: str, event_id: str) -> None:
    """Awaits an event's handling; an event no retry can handle is logged and acknowledged, so
    Pub/Sub doesn't deliver it again. Other failures raise, for Pub/Sub to retry."""
    try:
        await handling
    except Exception as error:
        if not final(error):
            raise

        logger.exception("Dropped event %s (%s): no retry can handle it", event_id, event_type)
