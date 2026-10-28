import json
from collections.abc import AsyncIterator
from uuid import UUID

from prepza_common.auth.user import User

from assistant.constants.actions_flow import CONFIRMED_NOTE
from assistant.constants.chat import HISTORY_CHARACTERS, HISTORY_MESSAGES
from assistant.constants.company_actions import CREATE_COMPANY
from assistant.models.answers import Turn
from assistant.repositories import messages
from assistant.services import actions
from assistant.services.chat import build_messages
from assistant.services.tenancy import user_companies
from assistant.services.turns import refuse_if_busy, stream


async def confirm(
    conversation_id: UUID,
    action_id: UUID,
    user: User,
    token: str,
    language: str,
    referral: str | None = None,
) -> AsyncIterator[str]:
    """Runs a confirmed action (actions.run), then streams like a message: the card's new state
    ({"action"}), and the assistant telling the user what happened. The result reaches the model
    only in this turn's prompt; it's never stored. Refused before the action runs while the
    instance is busy with turns."""
    refuse_if_busy()
    tool, pending, result, block = await actions.run(
        conversation_id, action_id, user, token, language, referral
    )
    company_id = UUID(pending["company_id"]) if pending["company_id"] else None
    # A company the action made is the user's now, for the tools that follow; any other action
    # leaves the list it was checked against.
    companies = await user_companies(user.uid, fresh=tool.name == CREATE_COMPANY)
    turn = Turn(
        conversation_id,
        user.uid,
        company_id,
        token,
        language,
        companies,
        user.name,
        new_question=False,
    )
    earlier = await messages.recent(conversation_id, HISTORY_MESSAGES)
    note = CONFIRMED_NOTE.format(
        tool=tool.name, result=json.dumps(result.content, ensure_ascii=False)
    )
    prompt = build_messages(turn, earlier, note, None, HISTORY_CHARACTERS)

    return stream(turn, prompt, {"action": block})
