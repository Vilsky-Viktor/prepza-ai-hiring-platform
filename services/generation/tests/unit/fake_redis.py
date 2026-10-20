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
        self.commands.append(lambda: self.redis.put(key, value, nx, ex))

    def incr(self, key):
        self.incrby(key, 1)

    def incrby(self, key, amount):
        def run():
            self.redis.counts[key] = self.redis.counts.get(key, 0) + amount

            return self.redis.counts[key]

        self.commands.append(run)

    def expire(self, key, seconds):
        self.commands.append(lambda: self.redis.expiries.update({key: seconds}) or True)

    def ttl(self, key):
        self.commands.append(lambda: self.redis.expiries.get(key, -2))

    async def execute(self):
        results = [command() for command in self.commands]
        self.commands = []

        return results


class FakeRedis:
    """Counters, their expiries and the limits' hash (`limits`, name to edited value); every
    call fails when `down`."""

    def __init__(self, limits: dict | None = None, down: bool = False):
        self.counts = {}
        self.expiries = {}
        self.limits = {name: str(value) for name, value in (limits or {}).items()}
        self.down = down

    def check(self):
        if self.down:
            raise ConnectionError("Redis is down")

    def put(self, key, value, nx, ex):
        if nx and key in self.counts:
            return None

        self.counts[key] = value
        self.expiries[key] = ex

        return True

    def pipeline(self, transaction):
        self.check()

        return FakePipeline(self)

    async def get(self, key):
        self.check()
        found = self.counts.get(key)

        return None if found is None else str(found).encode()

    async def set(self, key, value, nx=False, ex=None):
        self.check()

        return self.put(key, value, nx, ex)

    async def hgetall(self, key):
        self.check()

        return {name.encode(): value.encode() for name, value in self.limits.items()}

    async def exists(self, key):
        self.check()

        return int(key in self.counts)

    async def eval(self, script, numkeys, key, token):
        """Only the lock's release (storage/locks.py): deletes the key while it holds `token`."""
        self.check()

        if self.counts.get(key) == token:
            del self.counts[key]

            return 1

        return 0
