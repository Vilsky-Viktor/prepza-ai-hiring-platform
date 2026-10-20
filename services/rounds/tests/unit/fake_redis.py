class FakePipeline:
    """A Redis transaction in memory: the commands run in order on execute."""

    def __init__(self, redis):
        self.redis = redis
        self.commands = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def set(self, key, value, ex, nx):
        def run():
            if key in self.redis.counts:
                return None

            self.redis.counts[key] = value
            self.redis.expiries[key] = ex

            return True

        self.commands.append(run)

    def incrby(self, key, amount):
        def run():
            self.redis.counts[key] = self.redis.counts.get(key, 0) + amount

            return self.redis.counts[key]

        self.commands.append(run)

    def ttl(self, key):
        self.commands.append(lambda: self.redis.expiries.get(key, -2))

    async def execute(self):
        results = [command() for command in self.commands]
        self.commands = []

        return results


class FakeRedis:
    """Counters, their expiries and the limits' edited values (`limits`, name to value)."""

    def __init__(self):
        self.counts = {}
        self.expiries = {}
        self.limits = {}

    def pipeline(self, transaction):
        return FakePipeline(self)

    async def get(self, key):
        found = self.counts.get(key)

        return None if found is None else str(found).encode()

    async def hgetall(self, key):
        return {name.encode(): str(value).encode() for name, value in self.limits.items()}
