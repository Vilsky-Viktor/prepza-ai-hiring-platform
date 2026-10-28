"""Who may do what in a company, as companies answers it (prepza_common.auth.company_access):
billing checks it itself on a company's payment routes."""

from prepza_common.auth import company_access

from billing.config import settings
from billing.core.security import service_token


async def require(company_id, user_id: str, editor: bool = False) -> None:
    """A member may look; only an editor (owner or admin) may change. Otherwise a 404, as if
    the company weren't there, or a 403 for a viewer changing or a company that refuses it (an
    AI app it doesn't allow, a suspension)."""
    found = await company_access.access(
        settings.companies_url, service_token("companies"), company_id, user_id
    )
    company_access.require(found, editor)
