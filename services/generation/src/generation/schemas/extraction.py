from prepza_common.auth.user import Level
from pydantic import BaseModel, Field


class JobExtraction(BaseModel):
    title: str = Field(
        description="Short title for this test (max 60 characters): the role, and the company "
        "only in a company's own test."
    )
    requirements: list[str] = Field(
        description="Concrete, distinct requirements and qualifications from the posting."
    )
    level: Level = Field(description="Level of complexity based on required seniority.")
