from app.config.settings import settings
from app.models.email import Email


def sender(email: Email) -> str:
    """Who an email comes from: optional emails from their own subdomain, candidates' from
    theirs (the service sender until one is set), every other one from the service sender."""
    if email.optional:
        return settings.mail_from_updates

    if email.candidate and settings.mail_from_candidates:
        return settings.mail_from_candidates

    return settings.mail_from
