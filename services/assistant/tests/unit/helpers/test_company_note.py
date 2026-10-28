import uuid

from assistant.helpers.company_note import with_company_note
from assistant.models.answers import Turn
from assistant.models.tools import ToolResult

A, B = "8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f", "9d2e3c9f-2b3c-4d4e-9f0a-1b2c3d4e5f6a"
ALL_OF_TWO = Turn(uuid.uuid4(), "ann", None, "t", "en", frozenset({A, B}))
INTERVIEWS = ToolResult("list_interviews", {"company_id": A}, 200, {"data": []}, None, 0)


def test_with_all_companies_and_several_the_interviews_say_ask_which_company_first():
    content = with_company_note(INTERVIEWS, ALL_OF_TWO).content

    assert content["data"] == []
    assert content["note"].startswith("The user picked all companies and has 2.")


def test_no_note_with_a_company_picked_one_company_or_another_tool():
    picked = Turn(uuid.uuid4(), "ann", uuid.UUID(A), "t", "en", frozenset({A, B}))
    one = Turn(uuid.uuid4(), "ann", None, "t", "en", frozenset({A}))
    other = ToolResult("list_companies", {}, 200, {"data": []}, None, 0)

    assert with_company_note(INTERVIEWS, picked) is INTERVIEWS
    assert with_company_note(INTERVIEWS, one) is INTERVIEWS
    assert with_company_note(other, ALL_OF_TWO) is other
