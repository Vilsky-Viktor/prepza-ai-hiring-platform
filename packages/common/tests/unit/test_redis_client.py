from prepza_common.constants import (
    REDIS_HEALTH_CHECK_SECONDS,
    REDIS_RETRIES,
    REDIS_TIMEOUT_SECONDS,
)
from prepza_common.redis_client import redis_client
from redis.exceptions import ConnectionError, TimeoutError


def test_a_dropped_connection_is_retried_instead_of_failing_the_request():
    connection = redis_client("redis://localhost:6379").connection_pool.make_connection()

    assert connection.retry._retries == REDIS_RETRIES
    assert ConnectionError in connection.retry._supported_errors
    assert TimeoutError in connection.retry._supported_errors
    assert connection.health_check_interval == REDIS_HEALTH_CHECK_SECONDS


def test_connecting_and_every_command_have_a_short_timeout():
    connection = redis_client("redis://localhost:6379").connection_pool.make_connection()

    assert connection.socket_connect_timeout == REDIS_TIMEOUT_SECONDS
    assert connection.socket_timeout == REDIS_TIMEOUT_SECONDS
