# The database pool: generation and its worker each run on one instance with 2 connections of
# the shared budget, plus the checkpointer's own (CHECKPOINTER_POOL_SIZE).
DB_POOL_SIZE = 1
DB_MAX_OVERFLOW = 1
