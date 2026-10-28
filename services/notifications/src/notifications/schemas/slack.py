from pydantic import BaseModel


class SlackOut(BaseModel):
    """The company's Slack channel as the page shows it: never its web hook."""

    connected: bool
    status: str | None = None
    team: str | None = None
    channel: str | None = None
    # The kinds the channel gets, and every kind it could get, in order.
    kinds: list[str]
    all_kinds: list[str]


class SlackKindsIn(BaseModel):
    kinds: list[str]


class SlackStartOut(BaseModel):
    # Slack's page where the company approves and picks the channel.
    url: str
