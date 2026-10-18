from dataclasses import dataclass, field
from uuid import UUID

from app.models.tools import ToolResult


@dataclass
class Answer:
    """The assistant's answer as a turn builds it: its text so far, the blocks the panel shows,
    the tools it called and the tokens its model calls used."""

    parts: list[str] = field(default_factory=list)
    blocks: list[dict] = field(default_factory=list)
    results: list[ToolResult] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    # The actions it prepared, waiting for the user's confirmation (kept in Redis only).
    pending: list = field(default_factory=list)
    # What it showed with the `show` tool: "rows" and "link", one of each at most, and those
    # blocks, sent under the answer once it's written.
    shown: set = field(default_factory=set)
    shown_blocks: list = field(default_factory=list)
    # The Langfuse trace its model calls report to; None when Langfuse isn't set up.
    trace_id: str | None = None

    @property
    def content(self) -> str:
        return "".join(self.parts)

    @property
    def tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class Turn:
    """One message's turn: whose it is, in which conversation and language. The token is the
    user's own, which the tools send on; it's never stored, logged or shown to the model."""

    conversation_id: UUID
    user_id: str
    company_id: UUID | None
    token: str = field(repr=False)
    language: str
    # The ids of the user's companies, for their token: a tool naming another company is
    # refused before it's called.
    companies: frozenset[str] = frozenset()
    # The name on the user's account, if any: the model addresses them by it.
    user_name: str | None = None
    # A turn answering the user's new message (not one after a confirmed action): the
    # conversation's title may be refreshed after it.
    new_question: bool = True
