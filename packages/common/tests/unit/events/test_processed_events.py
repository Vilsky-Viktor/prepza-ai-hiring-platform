import asyncio

from testee_common.events.processed_events import claim


def test_a_change_not_from_an_event_is_always_new():
    # Nothing is noted: there's no id a redelivery could repeat.
    assert asyncio.run(claim(None, None, None)) is True
