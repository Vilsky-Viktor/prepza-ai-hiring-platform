from api.core.db import Session


async def transaction(call, *args):
    """Runs a repository function in a transaction of its own, as a service would, and gives its
    result."""
    async with Session.begin() as session:
        return await call(session, *args)
