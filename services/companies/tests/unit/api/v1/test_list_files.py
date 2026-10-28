"""A pasted or uploaded list: refused when it isn't a CSV or TXT file, isn't text or is too
large, and its unusable lines reported."""

from types import SimpleNamespace

import pytest

from companies.constants.invites import (
    FILE_TOO_LARGE,
    LIST_TOO_LONG,
    MAX_BULK_TEXT_LENGTH,
    NOT_A_LIST_FILE,
)
from companies.helpers.candidate_lists import read_list
from companies.helpers.list_files import list_refusal
from companies.services import candidate_invites
from tests.unit.api.v1.test_candidate_invites import INTERVIEW_ID, invite_setup

URL = f"/interviews/{INTERVIEW_ID}/candidates/bulk"


@pytest.mark.parametrize("filename", ["list.csv", "LIST.TXT", "my.list.Csv"])
def test_csv_and_txt_files_in_any_case_are_read(filename):
    assert list_refusal("ann@example.com", filename) is None


@pytest.mark.parametrize("filename", ["list.xlsx", "list", "list.csv.exe", "list.pdf"])
def test_other_files_are_refused(filename):
    assert list_refusal("ann@example.com", filename) == NOT_A_LIST_FILE


@pytest.mark.parametrize("text", ["PK\x03\x04\x00ann@example.com", "�" * 10 + "a@b.co"])
def test_a_renamed_binary_file_is_refused(text):
    assert list_refusal(text, "list.csv") == NOT_A_LIST_FILE


def test_a_file_over_the_limit_in_bytes_and_a_long_pasted_list_are_refused():
    # Under the limit in characters, over it in bytes.
    wide = "é" * (MAX_BULK_TEXT_LENGTH // 2 + 1)

    assert list_refusal(wide, "list.txt") == FILE_TOO_LARGE
    assert list_refusal(wide, None) is None
    assert list_refusal("a" * (MAX_BULK_TEXT_LENGTH + 1), None) == LIST_TOO_LONG


def test_each_unusable_line_is_given_once_with_its_main_reason():
    text = (
        "ann@example.com\n"
        "\n"  # empty: not counted
        "John Smith\n"
        "bob@example\n"
        "Bob <bob@example\n"  # an email that isn't valid comes first
        "Cid <cid@example.com\n"
        "dee@example.com, Dee Fox\n"
    )

    assert read_list(text) == (
        [("ann@example.com", None), ("dee@example.com", "Dee Fox")],
        [
            ("John Smith", "no_email"),
            ("bob@example", "invalid_email"),
            ("Bob <bob@example", "invalid_email"),
            ("Cid <cid@example.com", "unclear_name"),
        ],
    )


def test_a_csv_header_isnt_a_problem_and_its_rows_are_checked():
    text = "Name,Email\nAnn,ann@example.com\nNo Email,\n"

    assert read_list(text) == ([("ann@example.com", "Ann")], [("No Email,", "no_email")])


def test_the_list_endpoint_reports_unusable_lines_and_refuses_bad_files(client, monkeypatch):
    invite_setup(monkeypatch)

    async def invite(interview, company, user, email, name=None):
        return SimpleNamespace(id=None)

    monkeypatch.setattr(candidate_invites, "invite", invite)
    text = "ann@example.com\nnothing\nBob <bob@example.com\n"
    result = client.post(URL, json={"text": text}).json()

    assert result["invited"] == ["ann@example.com"]
    assert result["problems"] == [
        {"line": "nothing", "reason": "no_email"},
        {"line": "Bob <bob@example.com", "reason": "unclear_name"},
    ]

    # Only unusable lines: nobody is invited, and they're all said.
    only = client.post(URL, json={"text": "nothing here"}).json()

    assert only["invited"] == [] and only["problems"] == [
        {"line": "nothing here", "reason": "no_email"}
    ]

    refused = client.post(URL, json={"text": "ann@example.com", "filename": "list.xlsx"})

    assert (refused.status_code, refused.json()["detail"]) == (422, NOT_A_LIST_FILE)
