"""e2e_tests/browser-lock.sh: one browser run at a time, the waiting ones in the order they came."""

import subprocess
import time
from pathlib import Path

LOCK = Path(__file__).resolve().parents[2] / "e2e_tests" / "browser-lock.sh"


def until(check, seconds: float = 20) -> None:
    """Poll for a state instead of sleeping a fixed time."""
    end = time.monotonic() + seconds

    while not check():
        assert time.monotonic() < end, "timed out waiting"
        time.sleep(0.05)


def run(repo: Path, name: str) -> subprocess.Popen:
    """A browser run: takes the slot, notes its name, and holds the slot until `release-<name>`
    exists."""
    script = (
        f". {LOCK}; take_browser_slot; echo {name} >> got; "
        f"until [ -e release-{name} ]; do sleep 0.05; done"
    )

    return subprocess.Popen(
        ["bash", "-c", script],
        cwd=repo,
        env={
            "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
            "BROWSER_POLL_SECONDS": "0.05",
        },
        stderr=subprocess.DEVNULL,
    )


def test_waiting_runs_take_the_slot_in_the_order_they_came(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    got = tmp_path / "got"
    queue = tmp_path / ".git" / "prepza-browser-runs" / "queue"
    runs = [run(tmp_path, "first")]

    try:
        until(lambda: got.exists() and got.read_text().split() == ["first"])

        # Each later run starts once the one before it is queued, so the order is certain.
        for name in ["second", "third", "fourth"]:
            waiting = len(list(queue.iterdir()))
            runs.append(run(tmp_path, name))
            until(lambda w=waiting: len(list(queue.iterdir())) == w + 1)

        for name in ["first", "second", "third"]:
            (tmp_path / f"release-{name}").touch()

        until(lambda: len(got.read_text().split()) == 4)
        assert got.read_text().split() == ["first", "second", "third", "fourth"]
    finally:
        for name in ["first", "second", "third", "fourth"]:
            (tmp_path / f"release-{name}").touch()

        for process in runs:
            process.wait(timeout=20)


def test_a_waiting_run_that_died_does_not_hold_up_the_queue(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    got = tmp_path / "got"
    queue = tmp_path / ".git" / "prepza-browser-runs" / "queue"
    runs = [run(tmp_path, "first")]

    try:
        until(lambda: got.exists())
        dead = run(tmp_path, "dead")
        until(lambda: len(list(queue.iterdir())) == 1)
        runs.append(run(tmp_path, "later"))
        until(lambda: len(list(queue.iterdir())) == 2)
        dead.kill()
        dead.wait(timeout=20)
        (tmp_path / "release-first").touch()

        until(lambda: got.read_text().split() == ["first", "later"])
    finally:
        for name in ["first", "later"]:
            (tmp_path / f"release-{name}").touch()

        for process in runs:
            process.wait(timeout=20)


def test_a_stray_file_in_the_queue_does_not_let_a_run_skip_it(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    got = tmp_path / "got"
    queue = tmp_path / ".git" / "prepza-browser-runs" / "queue"
    runs = [run(tmp_path, "first")]

    try:
        until(lambda: got.exists())
        (queue / "001792674436-7365").touch()
        runs.append(run(tmp_path, "second"))
        until(lambda: any(entry.name.isdigit() for entry in queue.iterdir()))

        assert got.read_text().split() == ["first"]

        (tmp_path / "release-first").touch()
        until(lambda: got.read_text().split() == ["first", "second"])
    finally:
        for name in ["first", "second"]:
            (tmp_path / f"release-{name}").touch()

        for process in runs:
            process.wait(timeout=20)
