from datetime import UTC, datetime, timedelta

from assistant.constants.mcp import METADATA_DOCUMENT_SECONDS
from assistant.core.db import Session
from assistant.helpers.mcp_clients import document_client
from assistant.integrations import client_documents
from assistant.repositories import oauth


async def client_of(client_id: str) -> dict | None:
    """An app named by its Client ID Metadata Document: the copy kept while it's under a day
    old, else the document read again and kept. A document that can't be read leaves the kept
    copy in use; one that reads but isn't valid any more refuses the app."""
    async with Session() as session:
        kept = await oauth.read_document(session, client_id)

    now = datetime.now(UTC)

    if kept and now - kept[1] < timedelta(seconds=METADATA_DOCUMENT_SECONDS):
        return kept[0]

    document = await client_documents.read(client_id)

    if document is None:
        return kept[0] if kept else None

    client = document_client(client_id, document)

    if client is not None:
        async with Session.begin() as session:
            await oauth.keep_document(session, client_id, client, now)

    return client
