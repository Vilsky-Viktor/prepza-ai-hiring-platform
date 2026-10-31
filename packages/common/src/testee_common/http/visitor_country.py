from typing import Annotated

from fastapi import Header

# The visitor's country (two letters), which Google's load balancer sets on every request from
# a browser (the local gateway from a cookie), replacing any the browser sent. Optional: calls
# between services, AI apps, the public API and tests have none, and a saved currency (or US
# dollars) applies then. Declared `country: VisitorCountry = None`; an unknown or malformed
# value counts as none (billing checks it).
VisitorCountry = Annotated[str | None, Header(alias="X-Client-Country")]
