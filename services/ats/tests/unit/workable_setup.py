import uuid

from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from app.integrations import workable
from app.main import app

COMPANY_ID = uuid.uuid4()
OTHER_COMPANY = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()
THEIR_INTERVIEW = uuid.uuid4()
JOBS = [{"id": "A1", "name": "Accountant"}]
STAGES = [{"id": "assessment", "name": "Assessment"}]
# Workable's real job read, which the `stored` fixture replaces.
WORKABLE_JOB = workable.job


def sign_in(uid):
    app.dependency_overrides[current_user] = lambda: User(
        uid=uid, email=f"{uid}@example.com", email_verified=True
    )


def connect(client, token="good", account="acme.workable.com"):
    return client.put(
        f"/workable?company_id={COMPANY_ID}", json={"account": account, "token": token}
    )
