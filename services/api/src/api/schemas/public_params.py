# The public API's shared query and header parameters.
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Header, Query

UpdatedSince = Annotated[
    datetime | None,
    Query(
        description=(
            "Only items that changed at this time or later (ISO 8601), oldest change first: "
            "pass the last `updated_at` you got to sync"
        )
    ),
]
After = Annotated[
    UUID | None,
    Query(
        description=(
            "With `updated_since`: the `id` of the last item you got, so the next page starts "
            "after it and items changed at the same moment are neither repeated nor missed"
        )
    ),
]
# Retries are made safe here, without the client (services/idempotency.py); the header is still
# taken from integrations that send it, and left out of the docs.
IdempotencyKey = Annotated[str | None, Header(max_length=255, include_in_schema=False)]
