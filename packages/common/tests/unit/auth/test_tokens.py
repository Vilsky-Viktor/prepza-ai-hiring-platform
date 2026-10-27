import hashlib

from prepza_common.auth.tokens import hashed, new_token, purpose_key, same_secret


def test_a_new_token_has_its_prefix_and_is_kept_only_as_its_hash():
    token, stored = new_token("pzm_", 32)

    assert token.startswith("pzm_") and len(token) > 40
    assert stored == hashlib.sha256(token.encode()).hexdigest() == hashed(token)
    assert new_token("pzm_", 32)[0] != token


def test_a_secret_with_letters_beyond_ascii_is_just_not_the_same():
    """Text hmac.compare_digest would refuse with an error, a server error anyone could cause."""
    assert same_secret("abc", "abc") is True
    assert same_secret("äbc", "abc") is False


def test_a_purpose_key_is_its_own_for_each_use_and_isnt_the_secret():
    first = purpose_key("service-secret", "slack-state")

    assert first == purpose_key("service-secret", "slack-state")
    assert first not in {"service-secret", purpose_key("service-secret", "help-signatures")}
    assert first != purpose_key("another-secret", "slack-state")
