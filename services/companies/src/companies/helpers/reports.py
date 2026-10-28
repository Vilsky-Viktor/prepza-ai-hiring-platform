import base64
import binascii

from prepza_common.auth.user import User

from companies.constants.reports import MAX_REPORT_BYTES, PDF_SIGNATURE
from companies.models.interviews import Interview


def is_report_pdf(pdf: str) -> bool:
    """True when the base64 text is a PDF no larger than MAX_REPORT_BYTES."""
    try:
        content = base64.b64decode(pdf, validate=True)
    except binascii.Error:
        return False

    return len(content) <= MAX_REPORT_BYTES and content.startswith(PDF_SIGNATURE)


def report_sender(user: User, interview: Interview) -> dict:
    """Who an emailed report is from, as its email says: the member's name, replies to their
    address only when it's verified (otherwise to prepza's inbox), and its language."""
    return {
        "sender": user.name or user.email,
        "reply_to": user.email if user.email_verified else None,
        "language": user.language or interview.language,
    }
