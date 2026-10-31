from testee_common.auth.key_actor import key_actor
from testee_common.auth.user import User

from assistant.constants.key_tools import KEY_TOOLS
from assistant.constants.mcp import (
    KEY_CLIENT_NAME,
    KEY_MCP_PERMISSION,
    KEY_MISSING_PERMISSION,
    MCP_SCOPES,
)
from assistant.constants.tool_calls import UNKNOWN_TOOL
from assistant.core.caller import CALLER_IP
from assistant.helpers.oauth import resource_url
from assistant.integrations import api_keys
from assistant.models.oauth_tokens import Access


async def key_access(key: str) -> Access | None:
    """An AI agent's access with a company's API key, as the api service checked it: as the key
    itself (never the member who made it), in its company, with its permissions. None for a key that doesn't work or
    hasn't the mcp permission (the 401 an unknown token gets); the api's 403 for a key used from
    an address it doesn't allow."""
    found = await api_keys.verify(key, CALLER_IP.get())

    if found is None or KEY_MCP_PERMISSION not in found["permissions"]:
        return None

    return Access(
        token=key,
        client_id=found["id"],
        scopes=MCP_SCOPES,
        expires_at=None,
        resource=resource_url(),
        subject=key_actor(found["id"]),
        client_name=KEY_CLIENT_NAME,
        key_id=found["id"],
        company_id=found["company_id"],
        permissions=found["permissions"],
    )


def key_signed_in(access: Access) -> tuple[User, str]:
    """The key as the user its calls act as, and no token: each call carries one the assistant
    signs for its service (integrations/services.py)."""
    return User(uid=access.subject, email="", email_verified=True), ""


def key_may_use(access: Access, name: str) -> bool:
    """Whether the access may use the tool: an app always, a key with the tool's permission."""
    if access.key_id is None:
        return True

    return KEY_TOOLS.get(name) in access.permissions


def key_refusal(name: str) -> str:
    """Why a key may not use the tool: the permission it lacks, or, for a tool no key gets, that
    there's no such tool."""
    permission = KEY_TOOLS.get(name)

    return KEY_MISSING_PERMISSION.format(permission=permission) if permission else UNKNOWN_TOOL
