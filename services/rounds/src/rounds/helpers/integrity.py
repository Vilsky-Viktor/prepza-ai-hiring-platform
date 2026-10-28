from rounds.constants.integrity import MIN_TAB_LEAVE_SECONDS, IntegritySignal


def counted_leave(signal) -> bool:
    """A page leave that counts: one that lasted at least MIN_TAB_LEAVE_SECONDS, or that the
    candidate never came back from (its length unknown)."""
    if signal.kind != IntegritySignal.TAB_LEAVE:
        return False

    return signal.away_seconds is None or signal.away_seconds >= MIN_TAB_LEAVE_SECONDS
