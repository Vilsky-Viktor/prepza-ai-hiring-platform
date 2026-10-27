"""Hashes that stand for a person are keyed (prepza_common.auth.person_hash)."""

import hashlib

from prepza_common.auth.person_hash import digest, keyed, person_hash


def test_a_persons_hash_depends_on_the_key_so_a_list_of_addresses_cant_match_it():
    email = "ann@example.com"
    plain = hashlib.sha256(email.encode()).hexdigest()

    assert person_hash(email, "key-1") == person_hash(email, "key-1")
    assert person_hash(email, "key-1") != person_hash(email, "key-2")
    assert person_hash(email, "key-1") != plain
    assert len(person_hash(email, "key-1")) == 64


def test_a_stored_plain_digest_moves_to_the_same_keyed_hash_the_address_gets():
    email = "ann@example.com"

    assert digest(email) == hashlib.sha256(email.encode()).hexdigest()
    assert keyed(digest(email), "key-1") == person_hash(email, "key-1")
