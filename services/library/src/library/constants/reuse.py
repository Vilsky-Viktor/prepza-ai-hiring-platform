# Topics whose embeddings are within this cosine distance count as the same subject. Measured
# with text-embedding-3-small at 256 dimensions: the same subject in other words lands at
# 0.25-0.35, related but different subjects (bookkeeping vs financial statements) at 0.39-0.57.
MAX_TOPIC_DISTANCE = 0.35
# A question is proven, and can be reused, once answered this many times without a flag.
MIN_REUSE_ANSWERS = 5
MAX_REUSE_COUNT = 100
# Topics per request when embedding template topics that have none.
MAX_EMBEDDING_BATCH = 100
# A template topic is copied into a company's test only with at least this many company
# questions (as many as a candidate gets from a topic by default); a template with no such
# topic can't be copied.
MIN_COPY_QUESTIONS = 10
