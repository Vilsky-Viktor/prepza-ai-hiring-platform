import pytest
from testee_common.db import clean_start


@pytest.mark.parametrize(
    ("database_url", "redis_url"),
    [
        # A service's own (dev) database.
        ("postgresql+asyncpg://testee:secret@postgres/rounds", "redis://redis:6379/15"),
        # The dev Redis database.
        ("postgresql+asyncpg://testee:secret@postgres/rounds_test", "redis://redis:6379/0"),
    ],
)
def test_it_never_touches_anything_but_the_tests_own_databases(database_url, redis_url):
    with pytest.raises(RuntimeError):
        clean_start.start_clean(database_url, ["sessions"], redis_url)


def test_it_never_reads_a_dev_database():
    with pytest.raises(RuntimeError):
        clean_start.tables_left_empty("postgresql+asyncpg://testee:secret@postgres/rounds")
