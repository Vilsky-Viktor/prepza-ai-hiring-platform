from typing import Annotated

from fastapi import Query
from prepza_common.auth.service_auth import service_caller

from billing.config import settings
from billing.core.security import SERVICE_NAME

# The visitor's country, which the site or companies pass on from Google's load balancer;
# optional (calls without a visitor have none), and anything but a known two-letter code counts
# as none (helpers/currencies.py). Prices follow it where no currency is saved.
Country = Annotated[str | None, Query()]

# Calls to this service, signed with its own key.
ServiceCaller = service_caller(settings.service_secret, SERVICE_NAME)
