def test_hindi_says_api_key_not_api_of():
    """ "API की" reads as "of the API": a key is कुंजी (twice regressed)."""
    from prepza_common.i18n.messages.hi import MESSAGES

    assert [text for text in MESSAGES.values() if "API की" in text] == []
