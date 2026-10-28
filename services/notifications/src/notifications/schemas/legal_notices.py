from typing import Literal

from pydantic import BaseModel

from notifications.constants.legal_notices import LegalNoticeState


class LegalNoticeOut(BaseModel):
    document: str
    version: str
    state: LegalNoticeState
    # Who it goes to: every account, or every company's owners and admins.
    audience: Literal["everyone", "company_editors"]


class LegalChangeOut(BaseModel):
    """A document's new version, noticed and applying from `version` (a day)."""

    document: str
    version: str
