from companies.constants.monitoring import PASS_RATE_HIGH, PASS_RATE_LOW, PASS_RATE_MIN_FINISHED


def percent(part: int, whole: int) -> int | None:
    """`part` of `whole` in whole percent; None without a whole."""
    if whole == 0:
        return None

    return round(part * 100 / whole)


def outside_triggers(passed: int, finished: int) -> bool:
    """The monitoring plan's trigger, on exact counts so rounding never hides a case."""
    if finished < PASS_RATE_MIN_FINISHED:
        return False

    return passed * 100 < PASS_RATE_LOW * finished or passed * 100 > PASS_RATE_HIGH * finished
