from pydantic import BaseModel, ConfigDict, EmailStr, Field

from site_content.constants.contact import MAX_CONTACT_MESSAGE_LENGTH, MAX_CONTACT_NAME_LENGTH


class ContactRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=MAX_CONTACT_NAME_LENGTH)
    email: EmailStr
    message: str = Field(min_length=1, max_length=MAX_CONTACT_MESSAGE_LENGTH)
