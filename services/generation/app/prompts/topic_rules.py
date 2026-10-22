# What the topic draft and its revision share: the planner's role, and the message that sends a
# list over the limit back to merge.
# Who plans a test's topics, for the draft and its revision alike.
TOPICS_ROLE = (
    "You are an assessment designer who plans what a skills test for a job covers: the topics "
    "and subtopics its multiple-choice questions are written on."
)

TOO_MANY_TOPICS = """You returned {count} main topics, but the limit is {max_topics}. Return the
complete list again with at most {max_topics} main topics: combine the most closely related
topics into broader topics on their shared subject, keeping every subtopic that matters.
"""
