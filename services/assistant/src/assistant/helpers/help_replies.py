import hashlib
import hmac
from uuid import UUID

from prepza_common.auth.tokens import purpose_key, same_secret

from assistant.constants.help_chat import HELP_SIGNING_PURPOSE, HelpRole
from assistant.schemas.help_chat import HelpMessage


def help_signing_key(service_secret: str) -> str:
    """Signs the help chat's replies and votes: a key of its own, made from the service's, so a
    service holding the assistant's key to call it can't sign them."""
    return purpose_key(service_secret, HELP_SIGNING_PURPOSE)


def reply_signature(content: str, secret: str) -> str:
    """The signature the help chat gives a reply it wrote: the page sends it back with the reply,
    so a reply the page made up can't steer the next answer."""
    return hmac.new(secret.encode(), b"help-reply:" + content.encode(), hashlib.sha256).hexdigest()


def trusted(messages: list[HelpMessage], secret: str) -> list[HelpMessage]:
    """The conversation as the model may read it: every question, and only the replies the help
    chat signed itself."""
    return [
        message
        for message in messages
        if message.role == HelpRole.USER
        or same_secret(message.signature or "", reply_signature(message.content, secret))
    ]


def vote_signature(answer_id: UUID, trace_id: str | None, secret: str) -> str:
    """The signature the help chat gives an answer with its id and Langfuse trace: a vote on it
    must send it back, so only the page that got the answer can vote on it, on its own run."""
    signed = f"help-vote:{answer_id}:{trace_id or ''}".encode()

    return hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
