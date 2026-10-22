from pydantic import BaseModel, Field


class Error(BaseModel):
    """Every refusal's body: branch on `code`, show `detail`."""

    detail: str | list[dict] = Field(
        description=(
            "Why, for people, in the language of your `Accept-Language` header; never branch on "
            "it, as it can change. For `validation_failed`, a list with one entry per bad field, "
            "which its `loc` names"
        ),
        examples=["Interview not found"],
    )
    code: str = Field(
        description=(
            "What went wrong, as a stable machine-readable code to branch on; the list is in the "
            "description's Errors section. New codes can be added, so treat an unknown one by "
            "its HTTP status"
        ),
        examples=["not_found"],
    )
