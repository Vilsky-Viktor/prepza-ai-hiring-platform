"""The local Pub/Sub emulator keeps nothing over a restart, so its own container creates the topic
and subscriptions at every start and is healthy only once they exist; a one-off setup job would
leave a restarted emulator empty, and every event published after it lost."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def block(text: str, name: str) -> str:
    """A compose service's block, by its name."""
    found = re.search(rf"^  {name}:\n(.*?)(?=^  \S|\Z)", text, re.MULTILINE | re.DOTALL)
    assert found, name

    return found.group(1)


def test_the_emulator_creates_its_topic_and_subscriptions_at_every_start():
    pubsub = block((ROOT / "compose/infrastructure.yml").read_text(), "pubsub")

    assert "sh /pubsub-setup.sh && wait" in pubsub
    assert "./scripts/local/pubsub-setup.sh:/pubsub-setup.sh:ro" in pubsub
    assert re.search(r"healthcheck:\n.*subscriptions/", pubsub, re.DOTALL)


def test_services_wait_for_the_emulators_subscriptions_not_a_one_off_job():
    infrastructure = (ROOT / "compose/infrastructure.yml").read_text()
    migrate = block((ROOT / "compose/base.yml").read_text(), "migrate")

    assert not re.search(r"^  pubsub-setup:", infrastructure, re.MULTILINE)
    assert re.search(r"pubsub:\n\s+condition: service_healthy", migrate)
