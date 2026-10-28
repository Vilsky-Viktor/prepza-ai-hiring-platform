"""Which email setting changes are saved and logged, and on what basis (helpers/emails.py)."""

import pytest

from library.constants.emails import DEFAULTS, ConsentBasis, ConsentSource, EmailSetting
from library.helpers.emails import consent_changes

UPDATES, PROMOTIONS = EmailSetting.UPDATES, EmailSetting.PROMOTIONS


@pytest.mark.parametrize(
    ("current", "changes", "source", "new", "applied"),
    [
        # A setting already as asked changes nothing, so a repeat logs nothing.
        (DEFAULTS, {UPDATES: False}, ConsentSource.SETTINGS, False, []),
        (DEFAULTS, {UPDATES: True}, ConsentSource.SETTINGS, False, [(UPDATES, True, "choice")]),
        # A first sign-in turns updates on as a soft opt-in; a later one never does.
        (DEFAULTS, {UPDATES: True}, ConsentSource.SIGN_IN, True, [(UPDATES, True, "soft_opt_in")]),
        (DEFAULTS, {UPDATES: True}, ConsentSource.SIGN_IN, False, []),
        # Promotions ticked at a sign-in are the user's own choice.
        (
            DEFAULTS,
            {PROMOTIONS: True},
            ConsentSource.SIGN_IN,
            False,
            [(PROMOTIONS, True, "choice")],
        ),
    ],
)
def test_only_changes_that_change_something_are_kept_with_their_basis(
    current, changes, source, new, applied
):
    assert consent_changes(current, changes, source, new) == [
        (setting, on, ConsentBasis(basis)) for setting, on, basis in applied
    ]
