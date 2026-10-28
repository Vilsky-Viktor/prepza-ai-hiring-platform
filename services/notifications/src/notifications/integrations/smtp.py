import asyncio
import base64
import smtplib
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from notifications.config import settings
from notifications.constants.email import SEND_TIMEOUT_S
from notifications.helpers.senders import sender
from notifications.models.email import Email


def send_sync(email: Email) -> None:
    message = EmailMessage()
    message["From"] = sender(email)
    message["To"] = email.to
    message["Subject"] = email.subject
    message["Reply-To"] = email.reply_to or settings.contact_email
    # Resend adds these itself; an SMTP server may not.
    message["Date"] = formatdate()
    message["Message-ID"] = make_msgid()

    for name, value in email.headers.items():
        message[name] = value

    message.set_content(email.text)
    message.add_alternative(email.html, subtype="html")

    for name, content in email.attachments:
        message.add_attachment(
            base64.b64decode(content), maintype="application", subtype="pdf", filename=name
        )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=SEND_TIMEOUT_S) as client:
        client.send_message(message)


async def send(email: Email) -> None:
    await asyncio.to_thread(send_sync, email)
