from typing import Annotated

from fastapi import Query

# The visitor's country, which the site or companies pass on from Google's load balancer;
# optional (calls without a visitor have none), and anything but a known two-letter code counts
# as none (helpers/currencies.py). Prices follow it where no currency is saved.
Country = Annotated[str | None, Query()]
