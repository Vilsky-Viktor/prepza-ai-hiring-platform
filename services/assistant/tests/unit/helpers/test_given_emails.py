from assistant.helpers.given_emails import unknown_emails


def test_only_addresses_no_one_gave_are_unknown():
    arguments = {"email": "Lena.Fox@example.com", "text": "a@example.com, b@example.org", "x": 1}
    seen = "Invite lena.fox@example.com\n" + '{"data": [{"email": "a@example.com"}]}'

    assert unknown_emails(arguments, ("email", "text", "x"), seen) == ["b@example.org"]
    assert unknown_emails({"email": "email@example.com"}, ("email",), "Invite someone") == [
        "email@example.com"
    ]


def test_an_email_field_is_checked_whole_even_when_it_isnt_an_address():
    assert unknown_emails({"email": "?@example.com"}, ("email",), "Invite a candidate") == [
        "?@example.com"
    ]
