from library.constants.templates import MIN_INDEXABLE_TOPICS
from library.helpers.templates import is_indexable


def test_only_a_full_first_template_of_its_title_is_indexed():
    assert is_indexable(MIN_INDEXABLE_TOPICS, duplicate=False)
    # Too thin: one or two topics, as a demo template has.
    assert not is_indexable(MIN_INDEXABLE_TOPICS - 1, duplicate=False)
    # A later template with the same title.
    assert not is_indexable(MIN_INDEXABLE_TOPICS + 5, duplicate=True)
