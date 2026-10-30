from typing import Literal

from pydantic import BaseModel, Field

from rounds.constants.voice import Intent


class VoiceMatch(BaseModel):
    """What the model heard in a spoken answer (prompts/voice_match.py)."""

    intent: Intent = Field(
        description="choose, confirm, reject or unclear, as the instructions define them"
    )
    letters: list[Literal["A", "B", "C", "D"]] = Field(
        description="The options chosen, for choose; empty for any other intent"
    )


class VoiceAnswerOut(BaseModel):
    """A spoken answer, understood: what was heard (the candidate's own words, shown back to
    them and kept nowhere), what it meant, and the options it picks (indices, as a click sends
    them) for `choose` and `confirm`."""

    heard: str
    intent: Intent
    picks: list[int]
