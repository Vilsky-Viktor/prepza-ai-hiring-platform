import pytest
from cryptography.fernet import Fernet
from prepza_common.auth.encryption import decrypt, encrypt


def test_a_sealed_secret_is_unreadable_with_another_key():
    key = Fernet.generate_key().decode()
    sealed = encrypt(key, "secret-token")

    assert "secret-token" not in sealed
    assert decrypt(key, sealed) == "secret-token"
    assert decrypt(Fernet.generate_key().decode(), sealed) is None


@pytest.mark.parametrize("key", ["", "not-a-fernet-key"])
def test_a_missing_or_broken_key_reads_nothing(key):
    sealed = encrypt(Fernet.generate_key().decode(), "secret-token")

    assert decrypt(key, sealed) is None


def test_a_key_is_replaced_without_losing_what_the_old_one_sealed():
    old, new = Fernet.generate_key().decode(), Fernet.generate_key().decode()
    sealed_before = encrypt(old, "slack-token")
    rotating = f"{new}, {old}"
    sealed_after = encrypt(rotating, "ats-key")

    assert decrypt(rotating, sealed_before) == "slack-token"
    assert decrypt(rotating, sealed_after) == "ats-key"
    # Sealed with the new key: readable once the old one is gone.
    assert decrypt(new, sealed_after) == "ats-key"
    assert decrypt(new, sealed_before) is None
