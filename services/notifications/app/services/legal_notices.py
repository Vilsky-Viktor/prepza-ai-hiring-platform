from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from prepza_common.config.constants import LEGAL_VERSIONS

from app.constants.bulk import LEGAL_KINDS
from app.constants.legal_notices import (
    ALREADY_ASKED,
    EVERYONE,
    LEGAL_NOTICE_DAYS,
    TOO_LATE,
    LegalNoticeState,
)
from app.services.bulk import prepare_now
from app.services.bulk_content import document_of
from app.storage import bulk_recipients, bulk_sends


def earliest_version(today) -> str:
    """The earliest day a version can apply from to be noticed today."""
    return (today + timedelta(days=LEGAL_NOTICE_DAYS)).isoformat()


def kind_of(document: str) -> str:
    return f"legal_{document}"


async def states() -> list[dict]:
    """Each document's current version, and where its notice stands."""
    asked = {
        (document_of(send.kind), send.about): send
        for send in await bulk_sends.of_kinds(list(LEGAL_KINDS))
    }
    today = datetime.now(UTC).date()
    earliest = earliest_version(today)
    found = []

    for document, version in LEGAL_VERSIONS.items():
        send = asked.get((document, version))

        if send is not None:
            state = LegalNoticeState.SENT if send.finished_at else LegalNoticeState.SENDING
        elif version <= today.isoformat():
            state = LegalNoticeState.IN_FORCE
        elif version < earliest:
            state = LegalNoticeState.TOO_LATE
        else:
            state = LegalNoticeState.SENDABLE

        audience = "everyone" if document in EVERYONE else "company_editors"
        found.append(
            {"document": document, "version": version, "state": state, "audience": audience}
        )

    return found


async def ask(document: str, user_id: str) -> None:
    """A superadmin asks for the email about the document's current version: refused when it
    applies sooner than LEGAL_NOTICE_DAYS from now, or was asked for already. Its recipients
    are worked out now, and it goes in their bell; the sending hours' runs email it."""
    version = LEGAL_VERSIONS[document]

    if version < earliest_version(datetime.now(UTC).date()):
        raise HTTPException(status.HTTP_409_CONFLICT, TOO_LATE)

    if await bulk_sends.start(kind_of(document), version, user_id) is None:
        raise HTTPException(status.HTTP_409_CONFLICT, ALREADY_ASKED)

    await prepare_now(kind_of(document), version)


async def upcoming(user_id: str) -> list[dict]:
    """The legal changes noticed and not yet in force that concern the user, for the site's
    banner: the terms and the privacy policy for everyone, the DPA for those it was sent to."""
    today = datetime.now(UTC).date().isoformat()
    found = []

    for send in await bulk_sends.of_kinds(list(LEGAL_KINDS)):
        document = document_of(send.kind)

        if send.about <= today or LEGAL_VERSIONS.get(document) != send.about:
            continue

        if document in EVERYONE or await bulk_recipients.is_recipient(send.id, user_id):
            found.append({"document": document, "version": send.about})

    return found
