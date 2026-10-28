from assistant.helpers.trimming import trim


def test_only_allow_listed_keys_at_every_level_and_no_nulls():
    data = {
        "keys": [{"id": "k1", "name": "CI", "secret": "s"}],
        "webhooks": [{"id": "w1", "url": "https://x.example/secret", "failing": False}],
        "expiries": [30, 90],
        "name": None,
    }
    fields = frozenset({"keys", "webhooks", "id", "name", "failing"})

    assert trim(data, fields, 20, 300) == {
        "keys": [{"id": "k1", "name": "CI"}],
        "webhooks": [{"id": "w1", "failing": False}],
    }


def test_long_lists_are_cut_and_say_so():
    assert trim(list(range(5)), None, 3, 300) == {"items": [0, 1, 2], "shown": 3, "more": True}
    assert trim(list(range(3)), None, 3, 300) == [0, 1, 2]
    assert trim({"topics": [{"id": i} for i in range(4)]}, None, 2, 300) == {
        "topics": {"items": [{"id": 0}, {"id": 1}], "shown": 2, "more": True}
    }


def test_long_strings_are_cut():
    assert trim({"text": "a" * 10}, None, 20, 4) == {"text": "aaaa…"}
    assert trim("short", None, 20, 300) == "short"
