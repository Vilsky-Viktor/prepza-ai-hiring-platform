from notifications.repositories import notifications, opt_outs
from notifications.services import slack


async def handle(data: dict, event_id: str) -> None:
    """A deleted company's notifications, Slack connection and candidates' opt-outs go."""
    await notifications.remove_company(data["company_id"])
    await slack.disconnect(data["company_id"])
    await opt_outs.remove_company(data["company_id"])
