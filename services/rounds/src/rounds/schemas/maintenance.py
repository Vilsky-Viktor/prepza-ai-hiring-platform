from pydantic import BaseModel, Field


class RunningOut(BaseModel):
    running: int


class ResumeIn(BaseModel):
    # How long maintenance mode was on.
    seconds: float = Field(ge=0)
