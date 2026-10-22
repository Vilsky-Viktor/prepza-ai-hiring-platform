"""A list a user or a job reads is bounded: its storage function can't be called without a
limit."""

import inspect

import pytest

from app.storage import interviews


@pytest.mark.parametrize("read", [interviews.list_for_company])
def test_a_list_cant_be_read_without_a_limit(read):
    assert inspect.signature(read).parameters["limit"].default is inspect.Parameter.empty
