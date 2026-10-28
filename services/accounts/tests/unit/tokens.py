from datetime import UTC, datetime, timedelta

import jwt


def token(secret="test-secret-that-is-at-least-32-bytes", lifetime=60):
    """A call from another service (notifications) to accounts, signed with accounts' key."""
    exp = datetime.now(UTC) + timedelta(seconds=lifetime)

    return jwt.encode(
        {"iss": "notifications", "aud": "accounts", "exp": exp}, secret, algorithm="HS256"
    )
