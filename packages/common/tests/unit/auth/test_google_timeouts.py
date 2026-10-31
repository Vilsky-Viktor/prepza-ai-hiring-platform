"""Google's and Firebase's calls give up after GOOGLE_TIMEOUT_SECONDS, not their libraries' 120 s,
which outlasts every request."""

import firebase_admin
from testee_common.auth import auth, google
from testee_common.config.constants import GOOGLE_TIMEOUT_SECONDS


def test_firebase_admins_calls_have_the_short_timeout(monkeypatch):
    started = []
    monkeypatch.setattr(firebase_admin, "initialize_app", lambda options: started.append(options))

    auth.start_firebase("demo-project")

    assert started == [{"projectId": "demo-project", "httpTimeout": GOOGLE_TIMEOUT_SECONDS}]


def test_certificate_downloads_have_the_short_timeout_unless_a_call_sets_its_own(monkeypatch):
    sent = []

    def call(self, url, method="GET", body=None, headers=None, timeout=None, **kwargs):
        sent.append(timeout)

    monkeypatch.setattr(google.GoogleRequest, "__call__", call)
    request = google.TimedRequest()

    request("https://www.googleapis.com/oauth2/v1/certs")
    request("https://www.googleapis.com/oauth2/v1/certs", timeout=3)

    assert sent == [GOOGLE_TIMEOUT_SECONDS, 3]
