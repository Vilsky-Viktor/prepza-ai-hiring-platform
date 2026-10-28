import uuid

from companies.helpers.return_urls import with_invite


def test_the_return_address_names_the_invite():
    invite_id = uuid.uuid4()

    assert with_invite("https://acme.com/next?step=3", invite_id) == (
        f"https://acme.com/next?step=3&prepza_invite={invite_id}"
    )
