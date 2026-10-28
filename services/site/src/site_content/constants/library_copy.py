# The tables the one-off copy from library brings over (jobs/copy_from_library.py), with their
# columns and key, as library and site both have them; posts before their translations, which
# point at them.
LIBRARY_TABLES = {
    "news": (("id", "title", "text", "published_on", "created_at", "updated_at"), ("id",)),
    "news_translations": (("news_id", "language", "title", "text"), ("news_id", "language")),
}
# Rows read and written at once, each batch its own transaction.
COPY_BATCH = 1000
