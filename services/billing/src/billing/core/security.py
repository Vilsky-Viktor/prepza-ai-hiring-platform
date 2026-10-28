from prepza_common.auth.service_auth import callee_secret, issue_token

SERVICE_NAME = "billing"


def service_token(callee: str) -> str:
    """A token for calling `callee` (library, rounds, ...), signed with that service's key."""
    return issue_token(SERVICE_NAME, callee, callee_secret(callee))
