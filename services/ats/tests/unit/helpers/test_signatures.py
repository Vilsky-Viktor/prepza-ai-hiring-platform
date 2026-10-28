import base64
import time

from ats.helpers.ats import (
    breezy_signed,
    greenhouse_signed,
    recruitee_signed,
    teamtailor_signed,
    workable_signed,
)


def test_signatures_beyond_ascii_are_refused_not_an_error():
    """hmac.compare_digest refuses text that isn't ASCII with an error: a server error anyone
    could cause by sending one."""
    recent = base64.b64encode(f"t={int(time.time())},v2=ä".encode()).decode()

    assert workable_signed("token", b"{}", "ä") is False
    assert greenhouse_signed("secret", b"{}", "sha256 ä") is False
    assert teamtailor_signed("secret", b"{}", recent) is False
    assert recruitee_signed("secret", b"{}", "ä") is False
    assert breezy_signed("secret", b"{}", "ä") is False
