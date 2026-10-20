from dataclasses import replace

from app.constants.chat import INTERVIEWS_TOOL, WHICH_COMPANY_FIRST
from app.models.answers import Turn
from app.models.tools import ToolResult


def with_company_note(result: ToolResult, turn: Turn) -> ToolResult:
    """A company's interviews with "ask which company first" for the model when the user picked
    all companies and has several: the parent's order (company, then interview) is kept even
    when only one of them has interviews."""
    if result.tool != INTERVIEWS_TOOL or turn.company_id or len(turn.companies) < 2:
        return result

    note = WHICH_COMPANY_FIRST.format(count=len(turn.companies))

    return replace(result, content={**result.content, "note": note})
