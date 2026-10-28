from notifications.services import accounts


async def handle(data: dict, event_id: str) -> None:
    """A deleted company's notifications, Slack connection and candidates' opt-outs go."""
    await accounts.remove_company(data["company_id"])
