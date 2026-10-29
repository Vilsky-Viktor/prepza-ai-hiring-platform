"""What the action test (assistant_actions.py) adds to the page-context fixture
(assistant_fixture.py): an empty second company, a pending team member and two notes on the
Backend Developer interview; and every id the dataset's placeholders name."""

import uuid

from assistant_fixture import Fixture

MEMBER_EMAIL = "noor.member@example.com"
# The team's notes on the Backend Developer interview, the second the newest.
NOTES = (
    "Second-round interviews run on Thursdays with the hiring manager.",
    "Check two references before making an offer.",
)


async def extras(fixture: Fixture, facts: dict) -> dict:
    """What this test adds to the fixture, and every id the dataset's placeholders name."""
    owner = fixture.owner_token
    company = facts["company"]["id"]
    second = await fixture.api(
        "POST", "/companies/companies", owner, {"name": f"Eval Two {uuid.uuid4().hex[:6]}"}
    )
    body = {"email": MEMBER_EMAIL, "role": "viewer"}
    member = await fixture.api("POST", f"/companies/members?company_id={company}", owner, body)
    interviews = facts["interviews"]
    people = {row["name"]: row["id"] for item in interviews for row in item["candidates"]}
    notes = f"/companies/interviews/{interviews[0]['id']}/notes"
    note = await fixture.api("POST", notes, owner, {"text": NOTES[0]})
    note2 = await fixture.api("POST", notes, owner, {"text": NOTES[1]})

    return {
        "company": company,
        "company2": second["id"],
        "interview0": interviews[0]["id"],
        "interview1": interviews[1]["id"],
        "ann": people["Ann Lee"],
        "ben": people["Ben Ortiz"],
        "cara": people["Cara Diaz"],
        "member": member["id"],
        "note": note["id"],
        "note2": note2["id"],
    }
