from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Tool:
    """A tool the model may call, built from its allow-list entry and its route's snapshot."""

    name: str
    service: str
    method: str
    path: str
    path_params: tuple[str, ...]
    query_params: tuple[str, ...]
    # The function definition the model is given (OpenAI's tool format).
    definition: dict
    fields: frozenset[str] | None
    max_items: int
    max_length: int
    render: str | None
    link: str | None
    # A write: its body's fields, and the user confirms it first (a destructive one with a
    # warning); `preview` are the arguments the confirmation card shows.
    body_params: tuple[str, ...] = ()
    confirm: bool = False
    destructive: bool = False
    preview: tuple[str, ...] = ()
    # What the action is about, named on its card (see constants/actions.py), and the result's
    # field naming what it made.
    subject: dict | None = None
    credits: bool = False
    # A state that makes the action change nothing (auto top-up already off): read with the
    # user's token when it's prepared, it's refused instead of a card.
    done_when: dict | None = None
    result_label: str | None = None

    @property
    def parameters(self) -> dict:
        return self.definition["function"]["parameters"]


@dataclass(frozen=True)
class ToolResult:
    """One call's outcome: what the model reads, and the block the panel shows."""

    tool: str
    arguments: dict
    # The service's status; None when it didn't answer (or the arguments were refused).
    status_code: int | None
    # {"data", "source"} on success, {"error", "detail"} otherwise.
    content: dict
    block: dict | None
    duration_ms: int
    # A write waiting for the user's confirmation: the id its card confirms it by.
    action_id: UUID | None = None

    @property
    def succeeded(self) -> bool:
        return self.status_code is not None and 200 <= self.status_code < 300
