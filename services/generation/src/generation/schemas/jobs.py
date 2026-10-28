from uuid import UUID

from pydantic import BaseModel

from generation.constants.quality import QualityFlag


class RunGeneration(BaseModel):
    generation_id: UUID
    # The reviewed topics, when the job continues a generation after its review.
    resume: dict | None = None


class VerifyQuestion(BaseModel):
    question_id: UUID
    flag: QualityFlag
    now: bool = False
