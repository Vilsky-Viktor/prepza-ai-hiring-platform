class Pipeline:
    """Runs its commands one by one on the fake; their results, in order."""

    def __init__(self, redis):
        self.redis = redis
        self.commands = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def set(self, *args, **kwargs):
        self.commands.append(self.redis.set(*args, **kwargs))

    def incrby(self, key, amount):
        self.commands.append(self.redis.incrby(key, amount))

    def ttl(self, key):
        self.commands.append(self.redis.ttl(key))

    def sadd(self, *args):
        pass

    def expire(self, *args):
        pass

    async def execute(self):
        return [await command for command in self.commands]


class FakeRedis:
    """Redis's strings and counters with their expiry, and the limits' hash (`limits`, name to
    value), as the actions and the limits use them."""

    def __init__(self, limits: dict | None = None):
        self.values = {}
        self.expiry = {}
        self.limits = {name: str(value) for name, value in (limits or {}).items()}

    async def set(self, key, value, ex=None, nx=False):
        if nx and key in self.values:
            return None

        self.values[key] = value
        self.expiry[key] = ex

        return True

    async def get(self, key):
        return self.values.get(key)

    async def incrby(self, key, amount):
        self.values[key] = int(self.values.get(key, 0)) + amount

        return self.values[key]

    async def ttl(self, key):
        return self.expiry.get(key) or -2

    async def hgetall(self, key):
        return dict(self.limits) if key == "limits:values" else {}

    def pipeline(self, transaction=True):
        return Pipeline(self)

    async def getdel(self, key):
        self.expiry.pop(key, None)

        return self.values.pop(key, None)
