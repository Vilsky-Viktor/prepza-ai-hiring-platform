"""Redis in memory for unit tests, the one fake every service imports (each service's pytest
`pythonpath` includes this folder): strings and counters with their expiries (`counts`,
`expiries`), sets, the limits' hash (`limits`, name to value) and transactions. Every command
fails while `down`; DownRedis is one that is."""

from prepza_common.limit_list import LIMITS_KEY

MISSING = -2


class FakePipeline:
    """A Redis transaction in memory: the commands run in order on execute, each giving its
    result."""

    def __init__(self, redis):
        self.redis = redis
        self.commands = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def queue(self, command, *args, **kwargs):
        self.commands.append((command, args, kwargs))

    def set(self, *args, **kwargs):
        self.queue(self.redis.put, *args, **kwargs)

    def incr(self, key):
        self.queue(self.redis.add, key, 1)

    def incrby(self, key, amount):
        self.queue(self.redis.add, key, amount)

    def ttl(self, key):
        self.queue(self.redis.expiries.get, key, MISSING)

    def expire(self, key, seconds):
        self.queue(self.redis.expire_now, key, seconds)

    def sadd(self, key, *members):
        self.queue(self.redis.add_members, key, *members)

    def hset(self, key, mapping):
        self.queue(self.redis.limits.update, mapping)

    def delete(self, *keys):
        self.queue(self.redis.drop, *keys)

    async def execute(self):
        results = [command(*args, **kwargs) for command, args, kwargs in self.commands]
        self.commands = []

        return results


class FakeRedis:
    def __init__(self, limits: dict | None = None, down: bool = False):
        self.counts = {}
        self.expiries = {}
        self.sets = {}
        self.limits = dict(limits or {})
        self.down = down

    def check(self):
        if self.down:
            raise ConnectionError("Redis is down")

    # The commands' work, shared by the plain commands and the transaction's.

    def put(self, key, value, ex=None, nx=False, xx=False, keepttl=False):
        if (nx and key in self.counts) or (xx and key not in self.counts):
            return None

        self.counts[key] = value

        if not keepttl:
            self.expiries[key] = ex

        return True

    def add(self, key, amount):
        self.counts[key] = int(self.counts.get(key, 0)) + amount

        return self.counts[key]

    def expire_now(self, key, seconds):
        self.expiries[key] = seconds

        return True

    def add_members(self, key, *members):
        found = self.sets.setdefault(key, set())
        before = len(found)
        found.update(str(member).encode() for member in members)

        return len(found) - before

    def drop(self, *keys):
        gone = 0

        for key in keys:
            gone += int(
                self.counts.pop(key, None) is not None or self.sets.pop(key, None) is not None
            )
            self.expiries.pop(key, None)

        return gone

    # Redis's commands.

    def pipeline(self, transaction=True):
        self.check()

        return FakePipeline(self)

    async def get(self, key):
        self.check()
        found = self.counts.get(key)

        return None if found is None else str(found).encode()

    async def getdel(self, key):
        found = await self.get(key)
        self.drop(key)

        return found

    async def set(self, key, value, ex=None, nx=False, xx=False, keepttl=False):
        self.check()

        return self.put(key, value, ex, nx, xx, keepttl)

    async def incrby(self, key, amount):
        self.check()

        return self.add(key, amount)

    async def ttl(self, key):
        self.check()

        return self.expiries.get(key) or MISSING

    async def exists(self, key):
        self.check()

        return int(key in self.counts)

    async def delete(self, *keys):
        self.check()

        return self.drop(*keys)

    async def sadd(self, key, *members):
        self.check()

        return self.add_members(key, *members)

    async def smembers(self, key):
        self.check()

        return set(self.sets.get(key, set()))

    async def hgetall(self, key):
        self.check()

        if key != LIMITS_KEY:
            return {}

        return {name.encode(): str(value).encode() for name, value in self.limits.items()}

    async def eval(self, script, numkeys, key, token):
        """Only the lock's release (prepza_common.redis_lock): deletes the key while it holds
        `token`."""
        self.check()

        if self.counts.get(key) == token:
            self.drop(key)

            return 1

        return 0


class DownRedis(FakeRedis):
    """Redis that can't be reached."""

    def __init__(self, limits: dict | None = None):
        super().__init__(limits, down=True)
