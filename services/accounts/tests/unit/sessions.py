class FakeSessions:
    """The session factory without a database, for tests whose repositories are stubbed:
    `Session()` and `Session.begin()` both give a context with no session."""

    def __call__(self):
        return self

    def begin(self):
        return self

    async def __aenter__(self):
        return None

    async def __aexit__(self, *args):
        return False
