import uuid

from langchain_core.messages import AIMessage, HumanMessage

from assistant.helpers.history import history
from assistant.models.conversations import Message


def message(role, content):
    return Message(id=uuid.uuid4(), role=role, content=content)


def test_a_later_turn_reads_only_the_stored_text():
    rows = [message("user", "Who passed?"), message("assistant", "Ann passed.")]

    assert history(rows, 1_000) == [
        HumanMessage(content="Who passed?"),
        AIMessage(content="Ann passed."),
    ]


def test_a_failed_answer_without_text_adds_nothing():
    assert history([message("assistant", "")], 1_000) == []
