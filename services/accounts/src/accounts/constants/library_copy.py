# The tables the one-off copy from library brings over (jobs/copy_from_library.py), with their
# columns and key, as library and accounts both have them.
LIBRARY_TABLES = {
    "email_preferences": (
        (
            "user_id",
            "candidate_finished",
            "invite_undelivered",
            "ats_not_invited",
            "interview_ready",
            "reminders",
            "updates",
            "promotions",
            "updated_at",
        ),
        ("user_id",),
    ),
    "email_consents": (
        (
            "id",
            "user_id",
            "setting",
            "granted",
            "source",
            "basis",
            "text_version",
            "changed_by",
            "created_at",
        ),
        ("id",),
    ),
    "terms_acceptances": (("user_id", "version", "accepted_at"), ("user_id", "version")),
}
# Rows read and written at once, each batch its own transaction.
COPY_BATCH = 1000
