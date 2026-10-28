from prepza_common.config.settings import ServiceSettings


class Settings(ServiceSettings):
    # The API description lists every route, internal ones too: development only.
    api_docs: bool = False
    # The bell's notifications; Redis tells every open tab of a recipient at once.
    database_url: str
    redis_url: str
    # Signs calls from other services (library deletes and exports a user's notifications).
    service_secret: str
    # With a Resend key emails go out through Resend; without one, to the SMTP server (mailpit).
    resend_api_key: str = ""
    # Signs Resend's webhooks (bounces, complaints); without it every webhook is refused.
    resend_webhook_secret: str = ""
    smtp_host: str = "mailpit"
    smtp_port: int = 25
    # Resend sends only from a domain verified in its dashboard. Service emails (invites,
    # reports, billing) come from mail_from; emails a user may turn off (the digest, reminders)
    # from mail_from_updates, on a domain of their own, so spam complaints about them can't
    # hurt the service emails' reputation.
    mail_from: str = "prepza. <no-reply@prepza.local>"
    mail_from_updates: str = "prepza. <updates@mail.prepza.local>"
    # Candidates' emails (invites, reminders, a shareable link's own link), sent for many
    # companies to addresses they supply: their own sender, so one company's bad list can be
    # watched and kept apart. Empty: mail_from, until a subdomain of its own is verified.
    mail_from_candidates: str = ""
    # prepza's inbox: the contact page's messages go here, and replies to emails that have no
    # one else to answer (rather than to an unread no-reply address).
    contact_email: str = "hello@prepza.ai"
    # Public address of the site, used for links in emails.
    site_url: str
    # Signs the unsubscribe links in emails, so nobody can make one for someone else.
    email_link_secret: str
    # Keys the hashes candidates' opted-out and suppressed addresses are kept as
    # (prepza_common.auth.person_hash), so nobody with a list of addresses can match them.
    person_hash_key: str
    # Companies owns the invites, told when an invite's email wasn't delivered, and says which
    # companies a user belongs to, whose notifications they see.
    companies_url: str
    # Accounts keeps each user's address, language and email settings; an unsubscribe link turns
    # them off there. Library keeps the news the bell names.
    accounts_url: str
    library_url: str
    # Billing says which companies run low on credits, and generation which topics wait for a
    # review: the reminders. Generation also translates campaigns.
    billing_url: str
    generation_url: str
    # Rounds says who took a company's interview or a free practice round: a campaign's
    # candidates and learners.
    rounds_url: str
    # prepza's Slack app (api.slack.com: incoming-webhook scope), and the Fernet key that seals
    # each company's web hook. Without all three, Slack isn't offered.
    slack_client_id: str = ""
    slack_client_secret: str = ""
    slack_encryption_key: str = ""


settings = Settings()
