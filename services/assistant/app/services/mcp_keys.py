from app.constants.key_tools import KEY_TOOLS
from app.constants.mcp import (
    KEY_CLIENT_NAME,
    KEY_MCP_PERMISSION,
    KEY_MISSING_PERMISSION,
    MCP_SCOPES,
)
from app.constants.tool_calls import UNKNOWN_TOOL
from app.helpers.oauth import resource_url
from app.integrations import api_keys
from app.models.oauth_tokens import Access


async def key_access(key: str) -> Access | None:
    """An AI agent's access with a company's API key, as the api service checked it: as the
    key's maker, in its company, with its permissions. None for a key that doesn't work or
    hasn't the mcp permission (the 401 an unknown token gets)."""
    found = await api_keys.verify(key)

    if found is None or KEY_MCP_PERMISSION not in found["permissions"]:
        return None

    return Access(
        token=key,
        client_id=found["id"],
        scopes=MCP_SCOPES,
        expires_at=None,
        resource=resource_url(),
        subject=found["created_by"],
        client_name=KEY_CLIENT_NAME,
        key_id=found["id"],
        company_id=found["company_id"],
        permissions=found["permissions"],
    )


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
