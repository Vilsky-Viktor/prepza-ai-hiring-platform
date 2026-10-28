from datetime import timedelta

from fastapi import APIRouter, status

from rounds.api.dependencies import ServiceCaller
from rounds.core.db import Session
from rounds.repositories import running
from rounds.schemas.maintenance import ResumeIn, RunningOut
from rounds.services import maintenance

router = APIRouter(prefix="/internal/maintenance", tags=["internal"])


@router.get("/running")
async def running_interviews(caller: ServiceCaller) -> RunningOut:
    """For companies' maintenance switch: the candidates who may lose time if it's turned on."""
    async with Session() as session:
        return RunningOut(running=await running.running_interviews(session))


@router.post("/resume", status_code=status.HTTP_204_NO_CONTENT)
async def resume(body: ResumeIn, caller: ServiceCaller) -> None:
    """For companies' maintenance switch, before it turns off: running interviews get back the
    time it was on."""
    await maintenance.give_time_back(timedelta(seconds=body.seconds))
