"""The notes' authors as the Auth emulator knows them: a name, or the email without one, and the
picture; an account that's gone is left out."""

import asyncio
import os
import uuid

import firebase_admin
import pytest
from firebase_admin import auth as firebase_auth
from prepza_common.auth.auth import start_firebase

from accounts.services.accounts import profiles


@pytest.fixture
def people():
    """Two accounts of this test's own, one with a name and picture; deleted afterwards."""
    if not firebase_admin._apps:
        start_firebase(os.environ["FIREBASE_PROJECT_ID"])

    prefix = f"zz-test-{uuid.uuid4().hex}"
    named, unnamed = f"{prefix}-named", f"{prefix}-unnamed"
    firebase_auth.create_user(
        uid=named,
        email=f"{named}@example.com",
        display_name="Ann Lee",
        photo_url="https://example.com/ann.png",
    )
    firebase_auth.create_user(uid=unnamed, email=f"{unnamed}@example.com")

    yield named, unnamed

    firebase_auth.delete_users([named, unnamed])


def test_each_account_shows_by_name_or_email_and_one_gone_is_left_out(people):
    named, unnamed = people

    found = asyncio.run(profiles([named, unnamed, f"{named}-gone"]))

    assert sorted(found, key=lambda item: item["user_id"]) == [
        {"user_id": named, "name": "Ann Lee", "photo_url": "https://example.com/ann.png"},
        {"user_id": unnamed, "name": f"{unnamed}@example.com", "photo_url": None},
    ]
