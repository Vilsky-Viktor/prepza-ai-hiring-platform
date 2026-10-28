from library.constants.templates import MIN_INDEXABLE_TOPICS


def is_indexable(topic_count: int, duplicate: bool) -> bool:
    """Whether search engines should index a template's public pages: it covers at least
    MIN_INDEXABLE_TOPICS topics and is the first template of its title in its language (a later
    one with the same title is a near-duplicate of it)."""
    return topic_count >= MIN_INDEXABLE_TOPICS and not duplicate
