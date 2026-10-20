import hashlib
import hmac
import logging
import os
from datetime import UTC, datetime

from prepza_common.constants import FUNNEL_PREFIX, PUBLISH_IN_REQUEST_TIMEOUT_SECONDS
from prepza_common.pubsub import publish

logger = logging.getLogger(__name__)


def pseudonym(user_id: str) -> str | None:
    """The user as analytics knows them: a keyed hash (ANALYTICS_SALT), never the id or email.
    Pseudonymous: whoever holds the key can match it to an id. None without the key, as anyone
    with the ids could match an unkeyed hash."""
    salt = os.environ.get("ANALYTICS_SALT", "")

    if not salt:
        return None

    return hmac.new(salt.encode(), user_id.encode(), hashlib.sha256).hexdigest()[:32]


async def track(
    event: str,
    *,
    user_id: str | None = None,
    company_id: object | None = None,
    **props: object,
) -> None:
    """Records one funnel event (internal_docs/business/measurement.md). Best effort: it waits for Pub/Sub
    only as long as an in-request publish may, and a lost event is logged and never breaks the
    request. `props` hold counts and choices only, never text people wrote."""
    user = pseudonym(user_id) if user_id else None

    if user_id and user is None:
        logger.error("ANALYTICS_SALT isn't set: funnel event %s about a user not recorded", event)

        return

    data = {
        "at": datetime.now(UTC).isoformat(),
        "user": user,
        "company": str(company_id) if company_id else None,
        "props": props,
    }

    try:
        await publish(FUNNEL_PREFIX + event, data, PUBLISH_IN_REQUEST_TIMEOUT_SECONDS)
    except Exception:
        logger.warning("Couldn't record funnel event %s", event, exc_info=True)
