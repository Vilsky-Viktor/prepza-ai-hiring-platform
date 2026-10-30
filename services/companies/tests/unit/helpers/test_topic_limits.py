"""Each topic's number of questions a candidate gets: an even share of the cap for a new
interview, the room left for a topic added later."""

import pytest

from companies.constants.interviews import MAX_INTERVIEW_QUESTIONS
from companies.helpers.interviews import even_share, topic_limits


def topics(*sizes: int) -> list[tuple[str, int]]:
    return [(f"topic-{index}", size) for index, size in enumerate(sizes)]


@pytest.mark.parametrize(
    ("count", "share"),
    [(1, 10), (2, 10), (3, 10), (5, 10), (6, 10), (7, 8), (8, 7), (9, 6), (10, 6), (11, 5)]
    + [(12, 5)],
)
def test_a_new_interview_shares_the_cap_evenly(count, share):
    limits = topic_limits(topics(*[50] * count), {})

    assert even_share(count) == share
    assert list(limits.values()) == [share] * count
    assert sum(limits.values()) <= MAX_INTERVIEW_QUESTIONS


def test_a_small_topic_gives_all_it_has_and_its_spare_stays_unused():
    assert list(topic_limits(topics(3, 50, 0), {}).values()) == [3, 10, 0]


def test_a_stored_number_is_kept_and_capped_by_the_topic_size():
    stored = {"topic-0": 25, "topic-1": 40}

    assert topic_limits(topics(50, 30), stored) == {"topic-0": 25, "topic-1": 30}


@pytest.mark.parametrize(
    ("stored", "added"),
    [
        # 30 used: the new topic gets the default.
        ({"topic-0": 15, "topic-1": 15}, [10]),
        # 54 used: the 6 left.
        ({"topic-0": 30, "topic-1": 24}, [6]),
        # Full, or over the cap from before it: none.
        ({"topic-0": 30, "topic-1": 30}, [0]),
        ({"topic-0": 40, "topic-1": 40}, [0]),
    ],
)
def test_a_topic_added_later_gets_the_room_left(stored, added):
    limits = topic_limits(topics(50, 50, 50), stored)

    assert [limits["topic-2"]] == added


def test_topics_added_later_share_the_room_in_order():
    limits = topic_limits(topics(50, 50, 50, 50), {"topic-0": 45})

    assert list(limits.values()) == [45, 10, 5, 0]


def test_a_number_left_from_an_earlier_set_doesnt_count():
    """A regenerated topic has a new id: the old one's number is ignored."""
    assert topic_limits(topics(50, 50), {"gone": 60}) == {"topic-0": 10, "topic-1": 10}
