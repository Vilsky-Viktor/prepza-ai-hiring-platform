from prepza_common.ai.scope import SCOPE_RULE


def test_the_scope_rule_names_what_is_answered_and_how_the_rest_is_declined():
    assert "only questions and requests about prepza" in SCOPE_RULE
    assert "Kindly decline anything else" in SCOPE_RULE
    assert "Call no tools" in SCOPE_RULE
