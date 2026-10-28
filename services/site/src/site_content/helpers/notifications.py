from prepza_common.events.notifications import EVERYONE, NotificationKind, Recipient, notification


def news_notification(post) -> dict:
    """One notification for everyone, opening the post on the news page; the bell shows its
    title in each user's language (notifications asks for it)."""
    return notification(
        Recipient.ALL,
        EVERYONE,
        NotificationKind.NEWS,
        f"/news#{post.id}",
        key=str(post.id),
        news_id=str(post.id),
        title=post.title,
    )
