from langchain_core.messages import BaseMessage
from prepza_common.ai.llm import latest_messages

from assistant.constants.chat import Role
from assistant.helpers.page_context import describe_page
from assistant.models.conversations import Message
from assistant.prompts.assistant import EARLIER_PAGE


def history(messages: list[Message], room: int, with_pages: bool = False) -> list[BaseMessage]:
    """What the model reads of a conversation before a new message: the latest messages' text
    within `room` characters; `with_pages`, each of the user's starting with the page it was
    asked on. Tools' data isn't kept: the model calls them again when it needs it."""
    return latest_messages(
        [(item.role == Role.USER, text(item, with_pages)) for item in messages], room
    )


def text(message: Message, with_page: bool) -> str:
    if with_page and message.page:
        return EARLIER_PAGE.format(page=describe_page(message.page), message=message.content)

    return message.content
