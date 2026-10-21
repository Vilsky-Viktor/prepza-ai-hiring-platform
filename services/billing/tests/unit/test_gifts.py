import hashlib

from app.helpers.gifts import gift_key, inbox_of, legacy_gift_key

KEY = "test-person-hash-key"


def test_tags_case_and_gmail_dots_are_one_inbox():
    assert inbox_of(" Ann.Lee+2@GMail.com ") == "annlee@gmail.com"
    assert inbox_of("annlee@googlemail.com") == "annlee@gmail.com"
    assert gift_key("welcome", "ann.lee+x@gmail.com", KEY) == gift_key(
        "welcome", "annlee@gmail.com", KEY
    )


def test_dots_count_outside_gmail():
    assert inbox_of("ann.lee+jobs@acme.com") == "ann.lee@acme.com"
    assert gift_key("welcome", "ann.lee@acme.com", KEY) != gift_key(
        "welcome", "annlee@acme.com", KEY
    )


def test_a_gifts_key_is_keyed_so_a_list_of_addresses_cant_match_it():
    plain = hashlib.sha256(b"annlee@gmail.com").hexdigest()

    assert gift_key("welcome", "annlee@gmail.com", KEY) != f"welcome:{plain}"
    assert gift_key("welcome", "annlee@gmail.com", KEY) != gift_key(
        "welcome", "annlee@gmail.com", "another-key"
    )
    assert legacy_gift_key("welcome", "Ann@x.com ", KEY) == legacy_gift_key(
        "welcome", "ann@x.com", KEY
    )
