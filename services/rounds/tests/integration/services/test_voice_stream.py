"""Voice mode's live listening against the real database and Redis (services/voice_stream.py): the
candidate's own voice question is streamed, counted and its arrival noted for the time-up grace;
another user, a stale token and an interview not taken by voice are refused. The route itself is
a WebSocket, which the access matrix (httpx) can't call: this is its matrix. OpenAI faked."""

import asyncio
import json
import uuid
from contextlib import asynccontextmanager

import pytest
from prepza_common.auth.user import User
from sqlalchemy import update

from rounds.constants.voice import IN_TIME_KEY
from rounds.core.db import Session as Db
from rounds.core.db import engine
from rounds.integrations import library
from rounds.integrations.redis import get_redis
from rounds.models.sessions import Session
from rounds.services import voice_stream
from tests.integration.factories import created, topic

FRAME = bytes(1024)
ANSWER = [{"type": "start"}, FRAME, FRAME, {"type": "end", "waiting": []}]


class FakeSocket:
    """The browser's side: what it sends, in order, then it goes; what it got and the close."""

    def __init__(self, messages):
        self.inbox = list(messages)
        self.got = []
        self.code = None

    async def accept(self):
        pass

    async def receive(self):
        if not self.inbox:
            return {"type": "websocket.disconnect", "code": 1000}

        message = self.inbox.pop(0)

        if isinstance(message, bytes):
            return {"type": "websocket.receive", "bytes": message}

        return {"type": "websocket.receive", "text": json.dumps(message)}

    async def receive_text(self):
        return (await self.receive())["text"]

    async def send_json(self, data):
        self.got.append(data)

    async def close(self, code=1000):
        self.code = code


class FakeHearing:
    def __init__(self):
        self.sent = 0
        self.done = False
        self.seconds = 0.0

    async def send(self, pcm):
        self.sent += len(pcm)

    async def final(self):
        self.done, self.seconds = True, 1.0

        return "B"


@pytest.fixture(autouse=True)
def openai(monkeypatch):
    """Signing in takes the user's id as the token ("stale" is no one's); OpenAI hears "B"."""

    def verify(token, check_revoked=False):
        if token == "stale":
            return None

        return User(uid=token, email=f"{token}@example.com", email_verified=True)

    @asynccontextmanager
    async def live_hearing(language, keywords, model=None, delay=None):
        yield FakeHearing()

    async def english_set(set_id):
        return {"title": "Python", "language": "en"}

    monkeypatch.setattr(voice_stream, "verify", verify)
    monkeypatch.setattr(voice_stream, "live_hearing", live_hearing)
    monkeypatch.setattr(library, "get_set", english_set)


async def voice_question(user: str, voice=True) -> Session:
    """`user`'s running section of one question, shown and on its clock."""
    [row] = await created(user, uuid.uuid4(), [topic(size=1)], 60, company_id=uuid.uuid4())

    async with Db.begin() as db:
        await db.execute(
            update(Session)
            .where(Session.id == row.id)
            .values(voice=voice, question_shown_at=row.started_at)
        )

    return row


async def streamed(row: Session, token: str) -> FakeSocket:
    socket = FakeSocket([{"token": token}, *ANSWER])
    await voice_stream.stream(socket, row.id)

    return socket


@pytest.mark.parametrize(
    ("caller", "voice", "code"),
    [
        ("owner", True, 1000),
        ("someone else", True, 4404),
        ("signed out", True, 4401),
        ("owner", False, 4409),
    ],
)
def test_only_the_candidates_own_voice_question_is_streamed(run, caller, voice, code):
    owner = f"cand-{uuid.uuid4()}"

    async def scenario():
        row = await voice_question(owner, voice)
        token = {"owner": owner, "someone else": f"other-{uuid.uuid4()}"}.get(caller, "stale")
        socket = await streamed(row, token)
        redis = get_redis()
        noted = await redis.get(IN_TIME_KEY.format(session_id=row.id))
        answers = await redis.keys(f"rate:voice:answers:user:{owner}*")

        return socket, row, noted, answers

    socket, row, noted, answers = run(scenario())

    assert socket.code == code

    if code == 1000:
        [ready, answer] = socket.got
        assert ready == {"type": "ready"}
        assert answer["answer"] == {"heard": "B", "intent": "choose", "picks": [1], "clear": True}
        # Counted as an answer; its arrival noted, so its answer counts a little past the time.
        assert noted.decode() == row.questions[0]["id"]
        assert answers
    else:
        assert socket.got == []
        assert noted is None


class HeldSocket(FakeSocket):
    """A browser that says `start` and some audio, then holds the stream open until `go`."""

    def __init__(self, token, go):
        super().__init__([{"token": token}, {"type": "start"}, FRAME])
        self.go = go
        self.waiting = asyncio.Event()

    async def receive(self):
        if not self.inbox:
            self.waiting.set()
            await self.go.wait()
            self.inbox = [{"type": "end", "waiting": []}]

        return await super().receive()


def test_an_open_stream_holds_no_database_connection(run):
    """Streams last as long as the candidate speaks, and the pool is a few connections: more
    streams than it has, all open at once, hold none of them, and each still answers."""
    streams = engine.pool.size() + 3

    async def scenario():
        go = asyncio.Event()
        sockets = []

        for _ in range(streams):
            owner = f"cand-{uuid.uuid4()}"
            sockets.append((HeldSocket(owner, go), await voice_question(owner)))

        tasks = [asyncio.create_task(voice_stream.stream(s, row.id)) for s, row in sockets]
        await asyncio.wait_for(asyncio.gather(*(s.waiting.wait() for s, _ in sockets)), 10)
        held = engine.pool.checkedout()
        go.set()
        await asyncio.wait_for(asyncio.gather(*tasks), 10)

        return held, [s for s, _ in sockets]

    held, sockets = run(scenario())

    assert held == 0
    assert all(socket.code == 1000 for socket in sockets)
    assert all(socket.got[-1]["answer"]["heard"] == "B" for socket in sockets)
