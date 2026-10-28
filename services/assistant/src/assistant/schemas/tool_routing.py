from pydantic import BaseModel, Field

from assistant.constants.tool_groups import ToolGroup


class ToolRoute(BaseModel):
    groups: list[ToolGroup] = Field(
        description="The groups of tools the message may need, at most two; none when the "
        "core tools do."
    )
