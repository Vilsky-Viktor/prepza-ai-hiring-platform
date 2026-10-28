from accounts.constants.emails import ConsentBasis, ConsentSource, EmailSetting


def consent_changes(
    current: dict[str, bool], changes: dict[EmailSetting, bool], source: ConsentSource, new: bool
) -> list[tuple[EmailSetting, bool, ConsentBasis]]:
    """The changes that change something, each with its basis, so a repeated request logs
    nothing twice. A sign-in turns updates on only for a user whose preferences are `new`, the
    first time they see the opt-out: it never turns them back on for someone who turned them
    off."""
    applied = []

    for setting, on in changes.items():
        soft_opt_in = source == ConsentSource.SIGN_IN and setting == EmailSetting.UPDATES and on

        if current[setting] == on or (soft_opt_in and not new):
            continue

        applied.append(
            (setting, on, ConsentBasis.SOFT_OPT_IN if soft_opt_in else ConsentBasis.CHOICE)
        )

    return applied
