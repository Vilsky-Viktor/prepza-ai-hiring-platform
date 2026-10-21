import base64
import hashlib
import hmac
import json
import re
import time
from html.parser import HTMLParser

from prepza_common.constants import DEFAULT_LANGUAGE
from prepza_common.tokens import same_secret

from app.constants.ats import SUBDOMAIN, TEAMTAILOR_SIGNATURE_SECONDS
from app.templates.comments import COMMENTS


def subdomain(text: str, domain: str) -> str | None:
    """An account's subdomain from what a company pasted: "acme", "acme<domain>" (like
    acme.workable.com) or its full address; None when it isn't one."""
    value = text.strip().lower().removeprefix("https://").removeprefix("http://")
    value = value.split("/")[0].removesuffix(domain)

    return value if re.fullmatch(SUBDOMAIN, value) else None


# Tags that start a new line in plain text, and list items, which get a dash.
BLOCK_TAGS = {"p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "tr"}


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

        if tag == "li":
            self.parts.append("\n- ")

    def handle_endtag(self, tag: str) -> None:
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def html_to_text(html: str) -> str:
    """An ATS's HTML job text as plain text: paragraphs and list items on their own lines, at
    most one empty line between them."""
    parser = _Text()
    parser.feed(html or "")
    lines = [" ".join(line.split()) for line in "".join(parser.parts).splitlines()]
    text = "\n".join(lines)

    return re.sub(r"\n{3,}", "\n\n", text).strip()


def job_text(title: str, sections: list[str], limit: int) -> str:
    """A job as one plain text to make an interview from: its title, then each non-empty HTML
    section (description, requirements…), cut to `limit` characters."""
    parts = [title.strip(), *(html_to_text(section) for section in sections)]

    return "\n\n".join(part for part in parts if part)[:limit]


def workable_signed(token: str, body: bytes, signature: str) -> bool:
    """Whether a Workable event is Workable's: its X-Workable-Signature is the HMAC-SHA256 of
    the raw body with the account's token (hex, or base64)."""
    digest = hmac.new(token.encode(), body, hashlib.sha256).digest()
    given = signature.strip()

    return any(
        same_secret(given, expected)
        for expected in (digest.hex(), base64.b64encode(digest).decode())
    )


def greenhouse_signed(secret: str, body: bytes, signature: str) -> bool:
    """Whether a Greenhouse web hook is Greenhouse's: its Signature header is "sha256 " and the
    HMAC-SHA256 hex digest of the raw body with the secret key the company set."""
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    return same_secret(signature.strip().removeprefix("sha256 "), expected)


def teamtailor_signed(secret: str, body: bytes, signature: str) -> bool:
    """Whether a Teamtailor web hook is Teamtailor's, and new: its TT-Signature is base64 of
    "t=<timestamp>,v2=<hex>", the HMAC-SHA256 of "<timestamp>.<raw body>" with the signature key
    Teamtailor gave the web hook, signed within TEAMTAILOR_SIGNATURE_SECONDS of now (an older one
    is a replay)."""
    try:
        parts = dict(
            part.split("=", 1)
            for part in base64.b64decode(signature).decode().split(",")
            if "=" in part
        )
    except ValueError:
        return False

    if "t" not in parts or "v2" not in parts or not parts["t"].isdigit():
        return False

    if abs(time.time() - int(parts["t"])) > TEAMTAILOR_SIGNATURE_SECONDS:
        return False

    signed = parts["t"].encode() + b"." + body
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()

    return same_secret(parts["v2"], expected)


def recruitee_signed(secret: str, body: bytes, signature: str) -> bool:
    """Whether a Recruitee web hook is Recruitee's: its X-Recruitee-Signature is the HMAC-SHA256
    hex digest of the raw body with the secret Recruitee shows for the web hook."""
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    return same_secret(signature.strip().lower(), expected)


def breezy_signed(secret: str, body: bytes, signature: str) -> bool:
    """Whether a Breezy HR web hook is Breezy's: its X-Hook-Signature is the HMAC-SHA256 hex
    digest of the body with the web hook's secret. Breezy's docs sign the raw body in one place and
    the JSON written compactly in another, so either counts."""
    try:
        compact = json.dumps(json.loads(body), separators=(",", ":")).encode()
    except ValueError:
        compact = body

    given = signature.strip().lower()

    return any(
        same_secret(given, hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest())
        for signed in (body, compact)
    )


def result_comment(
    title: str,
    grade: int | None,
    passed: bool,
    flagged: bool,
    link: str,
    language: str | None,
) -> str:
    """The comment a finished candidate's results go back to the ATS as, in the interview's
    `language` (English when it's unknown)."""
    texts = COMMENTS.get(language or DEFAULT_LANGUAGE, COMMENTS[DEFAULT_LANGUAGE])
    lines = [f"prepza: {title}"]

    if grade is None:
        lines.append(texts["finished"])
    else:
        result = texts["passed"] if passed else texts["below"]
        lines.append(texts["grade"].format(grade=grade, result=result))

    if flagged:
        lines.append(texts["flagged"])

    lines.append(texts["decide"])
    lines.append(texts["scorecard"].format(link=link))

    return "\n".join(lines)


def verified_email(user) -> str:
    """The connecting user's email when verified: an unverified one could name someone else's
    ATS account, whom results would then be written back as."""
    return user.email if user.email_verified else ""
