from notifications.services import notices


async def handle(data: dict, event_id: str) -> None:
    """A deleted news post's notification for everyone goes."""
    await notices.remove_news(data["news_id"])
