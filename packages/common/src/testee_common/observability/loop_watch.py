"""Logs each time a service's event loop was blocked: a request that runs blocking code (a sync
call, a long computation) stops every other request of that instance until it's done. A task
beats every LOOP_BEAT_SECONDS; a thread notes where the loop is stuck once a beat is
LOOP_BLOCK_SECONDS late (unless the loop is only waiting for work), and the next beat logs how
long it was blocked and that place: files, lines and functions only, never values. A timer and a
sleeping thread, so it's always on."""

import asyncio
import logging
import sys
import threading
import time
import traceback
from collections.abc import Callable
from types import FrameType

from testee_common.config.observability_constants import (
    CODE_ROOTS,
    IDLE_FILE,
    LOOP_BEAT_SECONDS,
    LOOP_BLOCK_SECONDS,
    LOOP_STACK_FRAMES,
)

logger = logging.getLogger(__name__)


def short_path(path: str) -> str:
    """A file's path from its package on: the same in every image."""
    for root in CODE_ROOTS:
        if root in path:
            return path.rsplit(root, 1)[1]

    return path


def stack_summary(frame: FrameType) -> str:
    """Where `frame` is, innermost first: file, line and function of each frame, no values."""
    frames = traceback.extract_stack(frame)[-LOOP_STACK_FRAMES:]

    return " < ".join(f"{short_path(f.filename)}:{f.lineno} {f.name}" for f in reversed(frames))


def idle(frame: FrameType) -> bool:
    """Whether the loop's thread is waiting for its next event, in the selector."""
    return frame.f_code.co_filename.endswith(IDLE_FILE)


class LoopWatch:
    """The running loop's heartbeat (`beating`, a task on it) and its watcher (`watching`, a
    thread): where the loop was stuck, kept until the next beat logs it."""

    def __init__(self, block_seconds: float):
        self.block_seconds = block_seconds
        self.beat = time.monotonic()
        self.loop_thread = threading.get_ident()
        self.stuck_at: str | None = None
        self.stopped = threading.Event()

    async def beating(self) -> None:
        while True:
            now = time.monotonic()

            if self.stuck_at is not None:
                blocked = round((now - self.beat) * 1000)
                logger.warning("Event loop blocked for %d ms at %s", blocked, self.stuck_at)
                self.stuck_at = None

            self.beat = now
            await asyncio.sleep(LOOP_BEAT_SECONDS)

    def watching(self) -> None:
        while not self.stopped.wait(LOOP_BEAT_SECONDS):
            late = time.monotonic() - self.beat > self.block_seconds

            if late and self.stuck_at is None:
                frame = sys._current_frames().get(self.loop_thread)

                # Waiting for something to do isn't blocked: a late beat then only means the
                # instance had no CPU (Cloud Run throttles it between requests).
                if frame is not None and not idle(frame):
                    self.stuck_at = stack_summary(frame)


def start_loop_watch(block_seconds: float = LOOP_BLOCK_SECONDS) -> Callable[[], None]:
    """Starts watching the running loop; returns what stops it (at the service's shutdown)."""
    watch = LoopWatch(block_seconds)
    task = asyncio.get_running_loop().create_task(watch.beating())
    threading.Thread(target=watch.watching, name="loop-watch", daemon=True).start()

    def stop() -> None:
        watch.stopped.set()
        task.cancel()

    return stop
