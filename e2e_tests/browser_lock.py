#!/usr/bin/env python3
"""At most BROWSER_RUNS browser runs (default 2) use the local stack at once, whoever starts them,
and only runs of the same frontend share it: the test frontend is rebuilt when its files change,
which would break a run in progress on the build before.

Usage, from pages.sh and signed-in.sh (the slot is held for the script's pid, and the script frees
it when it exits; `source` names the frontend's files, e2e_tests/test_frontend.sh --source):

    browser_slot="$(python3 e2e_tests/browser_lock.py "$$" "$source")"
    trap 'rm -rf "$browser_slot"' EXIT

A run takes a free slot, a directory in the repo's git folder (shared by every worktree and every
agent's shell, whatever its TMPDIR) holding its pid and source, or waits for one; a slot whose run
is gone (killed, crashed) is taken over. A run waits while any live slot is another source's, and
a source ending in " alone" (a run with tests that change what every page sees) waits for every
other run to end, and keeps the others waiting while it runs.
Waiting runs queue in the order they started: each takes the next numbered ticket, and only the
lowest live ticket may take a slot, so no run waits behind later ones. mkdir is atomic, so this
needs no flock (which macOS lacks).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True

    return True


def gone(entry: Path) -> bool:
    """Whether a slot's or a ticket's run is gone: its pid is dead, or it has had no pid for a
    minute (a live run writes it at once)."""
    try:
        holder = (entry / "pid").read_text().strip()
    except OSError:
        holder = ""

    if holder:
        return not alive(int(holder))

    try:
        return time.time() - entry.stat().st_mtime > 60
    except OSError:
        return True


def tickets(queue: Path) -> list[int]:
    """The queue's tickets, lowest first: only plain numbers count, so anything else in the folder
    can't break the count."""
    return sorted(int(entry.name) for entry in queue.iterdir() if entry.name.isdigit())


def take(path: Path, pid: int) -> bool:
    try:
        path.mkdir()
    except FileExistsError:
        return False

    (path / "pid").write_text(f"{pid}\n")

    return True


def take_ticket(queue: Path, pid: int) -> Path:
    """The next number after every ticket in the queue, taken atomically."""
    number = max(tickets(queue), default=0) + 1

    while not take(queue / str(number), pid):
        number += 1

    return queue / str(number)


def first_ticket(queue: Path) -> Path | None:
    """The lowest ticket whose run is still alive; tickets of runs that are gone are removed."""
    for number in tickets(queue):
        ticket = queue / str(number)

        if not gone(ticket):
            return ticket

        shutil.rmtree(ticket, ignore_errors=True)

    return None


def live_slots(slots: Path) -> list[Path]:
    """The slots of runs still going; slots of runs that are gone are removed."""
    live = []

    for slot in slots.iterdir():
        if not slot.name.isdigit():
            continue

        if gone(slot):
            shutil.rmtree(slot, ignore_errors=True)
        else:
            live.append(slot)

    return live


def can_share(slots: Path, source: str) -> bool:
    """Whether this run may start beside the live ones: every one tests the frontend as `source`
    (a slot not yet written counts as another source, so the run waits a moment), and the run
    doesn't need the stack to itself (a source ending in " alone"; it then never matches)."""
    live = live_slots(slots)

    if not live:
        return True

    if source.endswith(" alone"):
        return False

    for slot in live:
        try:
            if (slot / "source").read_text().strip() != source:
                return False
        except OSError:
            return False

    return True


def take_slot(slots: Path, pid: int, most: int, source: str) -> Path | None:
    if not can_share(slots, source):
        return None

    for index in range(1, most + 1):
        slot = slots / str(index)

        if take(slot, pid):
            (slot / "source").write_text(f"{source}\n")

            return slot

    return None


def main(pid: int, source: str) -> int:
    common = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"], capture_output=True, text=True, check=True
    ).stdout.strip()
    slots = Path(common).resolve() / "testee-browser-runs"
    queue = slots / "queue"
    most = int(os.environ.get("BROWSER_RUNS", "2"))
    poll = float(os.environ.get("BROWSER_POLL_SECONDS", "5"))
    queue.mkdir(parents=True, exist_ok=True)
    ticket = take_ticket(queue, pid)
    waiting = False

    try:
        while alive(pid):
            first = first_ticket(queue) == ticket
            slot = take_slot(slots, pid, most, source) if first else None

            if slot:
                print(slot)

                return 0

            if not waiting:
                print(
                    f"waiting for earlier browser runs to end (BROWSER_RUNS={most} at once, "
                    "one frontend build at a time)",
                    file=sys.stderr,
                )
                waiting = True

            time.sleep(poll)

        return 1
    finally:
        shutil.rmtree(ticket, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else ""))
