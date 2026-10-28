import base64
import hashlib
import hmac
import time

import pytest

from ats.helpers.ats import teamtailor_signed


def signature(secret: str, body: bytes, timestamp: str | None = None) -> str:
    timestamp = timestamp or str(int(time.time()))
    signed = timestamp.encode() + b"." + body
    digest = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()

    return base64.b64encode(f"t={timestamp},v2={digest}".encode()).decode()


def test_only_bodies_signed_with_the_signature_key_count():
    body = b'{"event_name": "job_application.update"}'
    given = signature("secret", body)

    assert teamtailor_signed("secret", body, given)
    assert not teamtailor_signed("other", body, given)
    assert not teamtailor_signed("secret", body + b" ", given)


@pytest.mark.parametrize("age", [301, -301, 3600])
def test_a_signature_older_than_five_minutes_or_from_the_future_doesnt_count(age):
    body = b'{"event_name": "job_application.update"}'

    assert teamtailor_signed("secret", body, signature("secret", body, str(int(time.time()) - 290)))
    assert not teamtailor_signed(
        "secret", body, signature("secret", body, str(int(time.time()) - age))
    )


@pytest.mark.parametrize(
    "given",
    [
        "",
        "not base64!",
        base64.b64encode(b"\xff\xfe").decode(),
        base64.b64encode(b"t=1").decode(),
        base64.b64encode(b"v2=abc").decode(),
        base64.b64encode(b"t=soon,v2=abc").decode(),
    ],
)
def test_a_broken_or_incomplete_signature_counts_as_unsigned(given):
    assert not teamtailor_signed("secret", b"{}", given)
