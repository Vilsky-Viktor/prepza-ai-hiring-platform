import asyncio

import pytest

from generation.integrations import llm
from generation.prompts.topics import TOPICS_SYSTEM
from generation.schemas.topics import TopicList, TopicStructure
from generation.services.nodes.revision import revise_topics


def topic_list(count: int, subtopics: int) -> TopicList:
    return TopicList(
        topics=[
            TopicStructure(main_topic=f"Topic {i}", subtopics=[f"S{j}" for j in range(subtopics)])
            for i in range(count)
        ]
    )


class FakeStructured:
    """One topic more than `max_topics` until told the limit, each with `subtopics` subtopics."""

    def __init__(self, calls, max_topics, subtopics):
        self.calls = calls
        self.max_topics = max_topics
        self.subtopics = subtopics

    async def ainvoke(self, messages):
        self.calls.append(messages)

        if "but the limit is" in messages[-1].content:
            return topic_list(self.max_topics, self.subtopics)

        return topic_list(self.max_topics + 1, self.subtopics)


class FakeLLM:
    def __init__(self, calls, max_topics, subtopics=1):
        self.calls = calls
        self.max_topics = max_topics
        self.subtopics = subtopics

    def with_structured_output(self, schema):
        return FakeStructured(self.calls, self.max_topics, self.subtopics)


def revision_state(count: int) -> dict:
    return {
        "level": "medium",
        "requirements": ["Python"],
        "topics": [{"main_topic": f"Topic {i}", "subtopics": ["A"]} for i in range(count)],
        "feedback": "Add Flask basics",
    }


@pytest.mark.parametrize(("edited", "max_topics"), [({}, 10), ({"MAX_TOPICS": "4"}, 4)])
def test_revision_over_the_limit_is_sent_back_to_merge(monkeypatch, redis, edited, max_topics):
    """The limit is MAX_TOPICS as set in Controls when the revision runs."""
    calls = []
    redis.limits.update(edited)
    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: FakeLLM(calls, max_topics))

    result = asyncio.run(revise_topics(revision_state(max_topics)))

    assert len(result["topics"]) == max_topics
    assert len(calls) == 2
    assert f"in up to {max_topics} main topics" in calls[0][0].content
    assert f"You returned {max_topics + 1} main topics" in calls[1][-1].content


@pytest.mark.parametrize(("edited", "kept"), [({}, 5), ({"MAX_SUBTOPICS": "3"}, 3)])
def test_a_topic_keeps_at_most_max_subtopics(monkeypatch, redis, edited, kept):
    """MAX_SUBTOPICS as set in Controls when the topics are made."""
    calls = []
    redis.limits.update(edited)
    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: FakeLLM(calls, 10, subtopics=8))

    result = asyncio.run(revise_topics(revision_state(2)))

    assert all(topic["subtopics"] == [f"S{j}" for j in range(kept)] for topic in result["topics"])
    assert f"At most {kept} subtopics per main topic" in calls[0][0].content


def test_a_drafted_topic_keeps_at_most_max_subtopics():
    from generation.helpers.topics import fit_topics

    drafted = [{"main_topic": "SQL", "subtopics": [f"Subtopic {i}" for i in range(12)]}]

    assert fit_topics(drafted, 10)[0]["subtopics"] == [f"Subtopic {i}" for i in range(10)]


def test_the_plan_uses_every_topic_up_to_the_limit_it_includes():
    prompt = TOPICS_SYSTEM.format(max_topics=10, max_subtopics=10, max_name=60)

    assert "Up to 10 main topics, 10 included" in prompt
    assert "Never\n  merge distinct subjects to stay below the limit" in prompt
