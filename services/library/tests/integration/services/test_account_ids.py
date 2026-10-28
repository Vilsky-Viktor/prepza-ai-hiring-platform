import os
import uuid

import firebase_admin
import pytest
from firebase_admin import auth as firebase_auth
from prepza_common.auth.auth import start_firebase

from library.services.email_recipients import user_ids_after


@pytest.fixture
def accounts():
    """Three accounts of this test's own in the Auth emulator, their ids in order after
    `prefix`; deleted afterwards."""
    if not firebase_admin._apps:
        start_firebase(os.environ["FIREBASE_PROJECT_ID"])

    prefix = f"zz-test-{uuid.uuid4().hex}"
    uids = [f"{prefix}-{letter}" for letter in "abc"]

    for uid in uids:
        firebase_auth.create_user(uid=uid)

    yield prefix, uids

    firebase_auth.delete_users(uids)


def test_account_ids_go_on_a_page_at_a_time_after_the_last_one(accounts):
    """Firebase takes the last id of a page as the token of the next one."""
    prefix, uids = accounts

    assert user_ids_after(prefix, 2) == uids[:2]
    assert user_ids_after(uids[1], 2)[0] == uids[2]
