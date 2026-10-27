from prepza_common.auth.service_auth import callee_secret, issue_token, service_caller

from app.config.settings import settings

SERVICE_NAME = "api"


def service_token(callee: str) -> str:
    """A token for calling `callee` (companies), signed with that service's key."""
    return issue_token(SERVICE_NAME, callee, callee_secret(callee))


# Calls to this service, signed with its own key.
ServiceCaller = service_caller(settings.service_secret, SERVICE_NAME)
