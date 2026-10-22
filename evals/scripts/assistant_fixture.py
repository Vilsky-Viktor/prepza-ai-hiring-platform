"""The throwaway data the assistant's page-context test asks about, made and deleted through the
local stack as a user would (from inside the assistant's container): an owner with one company,
two interviews copied from the test's own templates (assistant_templates.py) and three
invited candidates who take them, aiming at set grades. Never the user's
own local records."""

import asyncio
import os
import random
import uuid

import httpx
import psycopg

API = "http://gateway/api"
AUTH = "http://firebase-auth:9199/identitytoolkit.googleapis.com/v1"
# Cloudflare Turnstile's dummy token: the local test secret passes it.
HEADERS = {"X-Human-Check": "XXXX.DUMMY.TOKEN.XXXX"}
PASSWORD = "secret123"
# Name, interview (0 the backend, 1 the data analyst) and the share of right answers aimed at.
CANDIDATES = (("Ann Lee", 0, 0.95), ("Ben Ortiz", 0, 0.35), ("Cara Diaz", 1, 0.7))
OWNER_NAME = "Dana Owner"
# What the judge is told of each candidate (and their topics' grades).
FACT_FIELDS = ("id", "name", "email", "status", "grade", "passed", "tab_leaves", "copies")
FACT_FIELDS += ("fast_answers",)
# The test's templates (assistant_templates.py makes them): title and topics.
TEMPLATES = (
    ("Backend Developer (eval)", ("SQL basics", "Indexes")),
    ("Data Analyst (eval)", ("Spreadsheets", "Statistics")),
)


def invite_token(invite_id: str) -> str:
    """The token in the invite link the candidate is emailed, read from the companies database
    as e2e_tests/flow.py does: the email itself isn't read."""
    url = os.environ["DATABASE_URL"].rsplit("/", 1)[0] + "/companies"

    with psycopg.connect(url) as connection:
        query = "SELECT token FROM candidate_invites WHERE id = %s"

        return connection.execute(query, (invite_id,)).fetchone()[0]


class Fixture:
    def __init__(self) -> None:
        self.http = httpx.AsyncClient(timeout=60, headers=HEADERS)
        # Every account made, as (local id, email): deleted in reverse, the owner last.
        self.accounts: list[tuple[str, str]] = []
        self.owner_email = ""
        self.owner_token = ""

    async def api(self, method: str, path: str, token: str, body=None):
        """A call as the user; over a rate limit (several runs in a row), again after a wait."""
        for wait in (10, 30, 60, 120, 0):
            response = await self.http.request(
                method, API + path, json=body, headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code != 429 or not wait:
                break

            await asyncio.sleep(wait)

        response.raise_for_status()

        return response.json() if response.content else None

    async def sign_up(self, name: str) -> tuple[str, str]:
        """A new emulator user with a verified email and a name; (email, ID token)."""
        email = f"eval-{name.split()[0].lower()}-{uuid.uuid4().hex[:8]}@example.com"
        body = {"email": email, "password": PASSWORD, "returnSecureToken": True}
        user = (await self.http.post(f"{AUTH}/accounts:signUp?key=demo", json=body)).json()
        project = os.environ["FIREBASE_PROJECT_ID"]
        await self.http.post(
            f"{AUTH}/projects/{project}/accounts:update",
            json={"localId": user["localId"], "emailVerified": True, "displayName": name},
            headers={"Authorization": "Bearer owner"},
        )
        self.accounts.append((user["localId"], email))

        return email, await self.token(email)

    async def token(self, email: str) -> str:
        """A fresh ID token (they last an hour)."""
        body = {"email": email, "password": PASSWORD, "returnSecureToken": True}
        url = f"{AUTH}/accounts:signInWithPassword?key=demo"

        return (await self.http.post(url, json=body)).json()["idToken"]

    async def take(self, interview_id: str, email: str, token: str, right: float, seed: int):
        """The owner invites the candidate, who takes the interview from the invite, answering
        about `right` of it correctly."""
        path = f"/companies/interviews/{interview_id}/candidates"
        invite = await self.api("POST", path, self.owner_token, {"email": email})
        # A first start takes the candidate's pledge to answer on their own.
        start = f"/companies/invites/{invite_token(invite['id'])}/start"
        started = await self.api("POST", start, token, {"pledged": True})
        session = started["sessions"][0]["id"]
        step = await self.api("POST", f"/rounds/sessions/{session}/step", token)
        luck = random.Random(seed)

        while not step["done"]:
            question = step["question"]
            options = question["options"]
            # A question that isn't the templates' own (the topic can get others) has no "Right"
            # option: the first one is taken.
            pick = next((i for i, text in enumerate(options) if text.startswith("Right")), 0)

            if luck.random() >= right:
                pick = (pick + 1) % len(options)
            body = {"question_id": question["question_id"], "option_index": pick}
            await self.api("POST", f"/rounds/sessions/{step['session']['id']}/answers", token, body)
            step = await self.api("POST", f"/rounds/sessions/{session}/step", token)

    async def create(self, template_ids: list[str]) -> dict:
        """The owner, company, interviews and candidates; the facts a judge checks answers
        against."""
        self.owner_email, self.owner_token = await self.sign_up(OWNER_NAME)
        owner = self.owner_token
        name = f"Eval Co {uuid.uuid4().hex[:6]}"
        company = await self.api("POST", "/companies/companies", owner, {"name": name})
        interviews = []

        for template_id in template_ids:
            path = f"/companies/interviews/from-template?company_id={company['id']}"
            interview = await self.api("POST", path, owner, {"template_id": template_id})
            interviews.append(interview)

        for seed, (person, index, right) in enumerate(CANDIDATES):
            email, token = await self.sign_up(person)
            await self.take(interviews[index]["id"], email, token, right, seed)

        return await self.facts(company, interviews)

    async def facts(self, company: dict, interviews: list[dict]) -> dict:
        """What the data is, once every candidate's result is in."""
        owner = self.owner_token
        found = []

        for interview in interviews:
            path = f"/companies/interviews/{interview['id']}/candidates"

            for _ in range(30):
                rows = await self.api("GET", path, owner)

                if all(row["status"] == "finished" for row in rows):
                    break

                await asyncio.sleep(2)
            found.append(
                {
                    "id": interview["id"],
                    "title": interview["title"],
                    "pass_mark": interview["pass_mark"],
                    "question_seconds": interview["question_seconds"],
                    "topics": TEMPLATES[len(found)][1],
                    "candidates": [
                        {
                            **{key: row[key] for key in FACT_FIELDS},
                            "sections": await self.sections(interview["id"], row["id"]),
                        }
                        for row in rows
                    ],
                }
            )

        credits = await self.api("GET", f"/companies/companies/{company['id']}/credits", owner)

        return {
            "owner": OWNER_NAME,
            "companies": 1,
            "company": {"id": company["id"], "name": company["name"]},
            "credits": credits,
            "interviews": found,
        }

    async def sections(self, interview_id: str, invite_id: str) -> list:
        """A candidate's grade in each topic, as their report shows it."""
        path = f"/companies/interviews/{interview_id}/candidates/{invite_id}"
        scorecard = await self.api("GET", path, self.owner_token)

        return [
            {"topic": item["topic_title"], "grade": item["final_score"]}
            for item in scorecard["sessions"]
        ]

    async def delete(self) -> None:
        """The accounts, as a user deletes theirs in settings (with the company they alone own
        and their data in every service), then their sign-ins; the owner last."""
        project = os.environ["FIREBASE_PROJECT_ID"]

        for local_id, email in reversed(self.accounts):
            try:
                await self.api("DELETE", "/library/me", await self.token(email))
            except httpx.HTTPError as error:
                print(f"clean-up: couldn't delete an account's data: {error}")
            await self.http.post(
                f"{AUTH}/projects/{project}/accounts:delete",
                json={"localId": local_id},
                headers={"Authorization": "Bearer owner"},
            )

        print(f"clean-up: {len(self.accounts)} throwaway accounts deleted")
        await self.http.aclose()
