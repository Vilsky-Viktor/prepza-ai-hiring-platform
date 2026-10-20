class FakePipeline:
    """The SET NX + INCRBY + TTL transaction of prepza_common.rate_limit, in memory."""

    def __init__(self, redis):
        self.redis = redis
        self.commands = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def set(self, key, value, ex, nx):
        self.commands.append(lambda: self.redis.counts.setdefault(key, value) and None)

    def incrby(self, key, amount):
        def run():
            self.redis.counts[key] = self.redis.counts.get(key, 0) + amount

            return self.redis.counts[key]

        self.commands.append(run)

    def ttl(self, key):
        # The seconds left in the window, which this fake doesn't keep.
        self.commands.append(lambda: 60)

    async def execute(self):
        results = [command() for command in self.commands]
        self.commands = []

        return results


class FakeRedis:
    """Counters, and the limits' edited values (`limits`, name to value) as billing keeps them."""

    def __init__(self, limits: dict | None = None):
        self.counts = {}
        self.limits = {name: str(value) for name, value in (limits or {}).items()}

    def pipeline(self, transaction):
        return FakePipeline(self)

    async def get(self, key):
        found = self.counts.get(key)

        return None if found is None else str(found).encode()

    async def exists(self, key):
        return int(key in self.counts)

    async def hgetall(self, key):
        return {name.encode(): value.encode() for name, value in self.limits.items()}
