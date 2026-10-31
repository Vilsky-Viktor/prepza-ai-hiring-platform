import asyncio
import logging

import httpx
import pytest
from sqlalchemy.exc import DataError, IntegrityError, NoResultFound, OperationalError
from starlette.exceptions import HTTPException
from testee_common.events.unhandleable import BadEvent, handle_or_drop


def answered(status):
    request = httpx.Request("GET", "http://companies/internal/members/m-1")

    return httpx.HTTPStatusError("failed", request=request, response=httpx.Response(status))


async def failing(error):
    raise error


@pytest.mark.parametrize(
    "error",
    [
        BadEvent("no sender"),
        KeyError("inviter"),
        TypeError("'NoneType' object is not subscriptable"),
        ValueError("badly formed hexadecimal UUID string"),
        DataError("SELECT", {}, Exception("invalid input syntax for type uuid")),
        IntegrityError("INSERT", {}, Exception("violates foreign key constraint")),
        NoResultFound(),
        answered(400),
        answered(404),
        answered(410),
        answered(422),
        HTTPException(404, "Company not found"),
    ],
)
def test_an_event_no_retry_can_handle_is_logged_and_acknowledged(error, caplog):
    with caplog.at_level(logging.ERROR):
        asyncio.run(handle_or_drop(failing(error), "member.invited", "e-1"))

    [record] = caplog.records
    assert record.levelno == logging.ERROR
    assert record.args == ("e-1", "member.invited")


@pytest.mark.parametrize(
    "error",
    [
        httpx.ConnectError("refused"),
        httpx.ReadTimeout("timed out"),
        TimeoutError(),
        ConnectionError("Redis went away"),
        OperationalError("SELECT", {}, Exception("the database system is starting up")),
        RuntimeError("anything else"),
        answered(401),
        answered(403),
        answered(409),
        answered(429),
        answered(500),
        answered(503),
        HTTPException(503, "Paused"),
    ],
)
def test_a_failure_a_retry_may_fix_raises_for_pub_sub_to_retry(error):
    with pytest.raises(type(error)):
        asyncio.run(handle_or_drop(failing(error), "member.invited", "e-1"))


def test_a_handled_event_logs_nothing(caplog):
    async def handled():
        return None

    asyncio.run(handle_or_drop(handled(), "member.invited", "e-1"))

    assert caplog.records == []
