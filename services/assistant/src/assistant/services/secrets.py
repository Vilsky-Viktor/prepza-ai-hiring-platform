from collections.abc import AsyncIterator

from testee_common.ai.secrets_check import (
    SECRET_PAGE_NAMES,
    SECRET_REMOVED,
    SECRET_REMOVED_ON_PAGE,
    Secret,
)
from testee_common.http.sse import sse_event
from testee_common.i18n.i18n import translate

from assistant.constants.show import PAGES
from assistant.helpers.blocks import link
from assistant.schemas.chat import ChatRequest

# The page of each form a secret belongs in (testee_common.ai.secrets_check's forms).
SECRET_PAGES = {"api": "api", "slack": "slack", "ats": "integrations"}


def secret_reply(secret: Secret, body: ChatRequest, language: str) -> AsyncIterator[str]:
    """A message with a secret, answered without anything else happening to it: not stored,
    not counted, never shown to the model or logged. The panel removes it from the chat
    ({"removed"}), and the fixed answer says why and names the page it belongs on, linked
    ("open API keys"), when there's one for the company the panel is about."""
    page = SECRET_PAGES.get(secret.form or "")
    company_id = str(body.company_id) if body.company_id else None
    url = link(PAGES[page], {"company_id": company_id}) if page else None
    text = translate(SECRET_REMOVED_ON_PAGE[secret.form] if url else SECRET_REMOVED, language)
    label = translate(SECRET_PAGE_NAMES[secret.form], language) if url else None

    async def events():
        yield sse_event({"removed": True})
        yield sse_event({"delta": text})

        if url:
            link_block = {"kind": "link", "items": [], "links": [url], "page": page, "label": label}
            yield sse_event({"block": link_block})

        yield sse_event({"done": {"message_id": None}})

    return events()
