from uuid import UUID

from pydantic import BaseModel


class PassRateOut(BaseModel):
    """One company interview with finished candidates, for the superadmin's monitoring."""

    interview_id: UUID
    title: str | None
    company: str
    finished: int
    # Percent of finished candidates at or above the interview's pass mark, as it is now.
    pass_rate: int
    pass_mark: int
    average_grade: int
    # Percent of the interview's answers whose time ran out; None before any answer.
    timeout_share: int | None
    # Outside the monitoring plan's trigger range: worth a look.
    outside_triggers: bool


class PauseIn(BaseModel):
    paused: bool


class PauseOut(BaseModel):
    paused: bool


class MaintenanceIn(BaseModel):
    on: bool


class MaintenanceOut(BaseModel):
    on: bool
    # Whoever asks is a superadmin: the site stays open to them while it's on.
    superadmin: bool = False


class MaintenanceSwitchOut(BaseModel):
    on: bool
    # Candidates in an interview now, who may lose time while it's on; None when rounds didn't
    # answer.
    running: int | None
