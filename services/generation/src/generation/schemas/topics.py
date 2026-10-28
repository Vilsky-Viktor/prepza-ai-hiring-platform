from pydantic import BaseModel, Field


class TopicStructure(BaseModel):
    main_topic: str = Field(description="Main topic of the test")
    subtopics: list[str] = Field(description="Subtopics of the main topic")


class TopicList(BaseModel):
    topics: list[TopicStructure] = Field(description="The test's topics.")
