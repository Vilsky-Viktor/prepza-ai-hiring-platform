from prepza_common.auth.service_auth import service_caller

from accounts.config import settings
from accounts.core.security import SERVICE_NAME

# Calls to this service, signed with its own key.
ServiceCaller = service_caller(settings.service_secret, SERVICE_NAME)
