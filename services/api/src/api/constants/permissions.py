from enum import StrEnum


# What an API key may do, ticked when it's made; each public route needs one.
class Permission(StrEnum):
    INTERVIEWS_READ = "interviews:read"
    INTERVIEWS_CREATE = "interviews:create"
    CANDIDATES_READ = "candidates:read"
    CANDIDATES_INVITE = "candidates:invite"
    CANDIDATES_CHANGE = "candidates:change"
    CANDIDATES_DELETE = "candidates:delete"
    CREDITS_READ = "credits:read"
    # Use the key with AI agents, at the MCP server.
    MCP = "mcp"


# The permissions by what they touch, in the order the API page shows them.
PERMISSION_GROUPS = {
    "interviews": [Permission.INTERVIEWS_READ, Permission.INTERVIEWS_CREATE],
    "candidates": [
        Permission.CANDIDATES_READ,
        Permission.CANDIDATES_INVITE,
        Permission.CANDIDATES_CHANGE,
        Permission.CANDIDATES_DELETE,
    ],
    "credits": [Permission.CREDITS_READ],
    "ai_agents": [Permission.MCP],
}
# A permission that changes something comes with reading what it changes.
IMPLIED = {
    Permission.INTERVIEWS_CREATE: Permission.INTERVIEWS_READ,
    Permission.CANDIDATES_INVITE: Permission.CANDIDATES_READ,
    Permission.CANDIDATES_CHANGE: Permission.CANDIDATES_READ,
    Permission.CANDIDATES_DELETE: Permission.CANDIDATES_READ,
}
# What a new key starts with: reading interviews and candidates, nothing that changes or costs.
DEFAULT_PERMISSIONS = [Permission.INTERVIEWS_READ, Permission.CANDIDATES_READ]

# The answer to a route the key may not call: its code, and its message with the permission.
MISSING_PERMISSION = "missing_permission"
MISSING_PERMISSION_MESSAGE = "This API key doesn't have the {permission} permission."
ONLY_NARROWING = "A key's permissions can only be narrowed; make a new key to add one."
