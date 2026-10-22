# Shortened embeddings: plenty to tell topics apart, and small to store. Library's column matches.
EMBEDDING_DIMENSIONS = 256
# Reused questions fill at most this share of a topic; the rest are always new.
MAX_REUSE_SHARE = 0.5
# Topics per request when embedding template topics that have none; library accepts at most 100.
EMBEDDING_BATCH_SIZE = 100
