from testee_common.auth.service_auth import callee_secret, issue_token

SERVICE_NAME = "assistant"


def service_token(callee: str, issuer: str = SERVICE_NAME, extra: dict | None = None) -> str:
    """A token for calling `callee`, signed with that service's key. Companies reads it in the
    X-Assistant header, to audit the reads made through the assistant (or, issued as "mcp",
    through an AI app) as such, and with `extra` an API key's company and id: it refuses any
    other company."""
    return issue_token(issuer, callee, callee_secret(callee), extra)
