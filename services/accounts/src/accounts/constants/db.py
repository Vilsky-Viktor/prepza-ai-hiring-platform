# The database pool: accounts runs on one instance with 1 connection of the shared budget. Its
# requests mostly wait on other services (deletion and export) or read a row or two.
DB_POOL_SIZE = 1
DB_MAX_OVERFLOW = 0
