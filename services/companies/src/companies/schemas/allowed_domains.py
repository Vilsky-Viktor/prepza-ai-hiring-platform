from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, StringConstraints

from companies.constants.allowed_domains import MAX_ALLOWED_DOMAINS, MAX_DOMAIN_LENGTH
from companies.helpers.allowed_domains import normalized


class AllowedDomains(BaseModel):
    """The sites that may embed the company's interviews with the SDK, kept lowercase without a
    scheme, each once (422 naming a bad one); and whether the developer's own computer
    (localhost, any port) may too."""

    domains: Annotated[
        list[Annotated[str, StringConstraints(max_length=MAX_DOMAIN_LENGTH)]],
        Field(max_length=MAX_ALLOWED_DOMAINS),
        AfterValidator(normalized),
    ]
    allow_localhost: bool = False
