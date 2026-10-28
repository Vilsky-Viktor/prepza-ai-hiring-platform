"""A step that fails, for the one-save tests: patched over an action's later step, it shows
that nothing the earlier steps wrote is kept."""


class DatabaseWentAway(RuntimeError):
    pass


async def broken(*args, **kwargs):
    raise DatabaseWentAway("The database went away")


def broken_now(*args, **kwargs):
    raise DatabaseWentAway("The database went away")
