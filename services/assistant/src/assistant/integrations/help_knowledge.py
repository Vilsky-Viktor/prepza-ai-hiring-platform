from prepza_common.http import http
from prepza_common.http.http import bearer

from assistant.config import settings
from assistant.constants.help_chat import KNOWLEDGE_PATH
from assistant.core.security import service_token
from assistant.schemas.help_chat import HelpKnowledge


async def help_knowledge(country: str | None, page: str | None) -> HelpKnowledge:
    """What the help chat answers from, from rounds (which owns the site's documents): the
    platform guide with the prices in the currency of the visitor's `country`, and the guide of
    the `page` asked on. Raises when rounds doesn't answer."""
    query = {key: value for key, value in {"country": country, "page": page}.items() if value}
    response = await http.get_client().get(
        settings.rounds_url + KNOWLEDGE_PATH,
        params=query,
        headers=bearer(service_token("rounds")),
    )
    response.raise_for_status()

    return HelpKnowledge.model_validate(response.json())
