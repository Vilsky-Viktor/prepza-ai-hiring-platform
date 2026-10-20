class FakePipeline:
    """The SET NX + INCRBY + TTL transaction of prepza_common.rate_limit, in memory."""

    def __init__(self, redis):
        self.redis = redis
        self.adds = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def set(self, key, value, ex, nx):
        self.redis.counts.setdefault(key, value)

    def incrby(self, key, amount):
        self.adds.append((key, amount))

    def ttl(self, key):
        pass

    async def execute(self):
        key, amount = self.adds.pop()
        self.redis.counts[key] += amount

        # The seconds left in the window, which this fake doesn't keep, come last.
        return [True, self.redis.counts[key], 60]


class FakeRedis:
    """Counters, and the limits' edited values (`limits`, name to value)."""

    def __init__(self, limits: dict | None = None):
        self.counts = {}
        self.limits = {name: str(value) for name, value in (limits or {}).items()}

    def pipeline(self, transaction):
        return FakePipeline(self)

    async def hgetall(self, key):
        return {name.encode(): value.encode() for name, value in self.limits.items()}
