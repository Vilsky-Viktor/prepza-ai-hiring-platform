import uuid

import httpx
import pytest
from prepza_common.http import http

from ats.integrations import workable
from ats.repositories import ats_links
from tests.unit.workable_setup import (
    COMPANY_ID,
    INTERVIEW_ID,
    JOBS,
    THEIR_INTERVIEW,
    WORKABLE_JOB,
    connect,
    sign_in,
)


def test_a_job_links_to_one_of_the_companys_interviews(client, stored, key):
    sign_in("ann")
    connect(client)
    body = {"provider": "workable", "job_id": "A1", "stage_id": "assessment"}

    assert client.get(f"/workable/jobs?company_id={COMPANY_ID}").json() == JOBS
    assert (
        client.post(
            f"/links?company_id={COMPANY_ID}",
            json={**body, "interview_id": str(INTERVIEW_ID)},
        ).status_code
        == 201
    )
    # Linked as Ann's, for the action log.
    assert stored["links"] == [(INTERVIEW_ID, "A1", "assessment", "ann")]
    # Linking reads the one job, not the whole list again.
    assert stored["read"] == ["every job", "A1"]
    # Workable notifies this link's own address, and the subscription is kept to cancel it.
    assert stored["targets"][0].startswith("http://localhost:8090/api/ats/webhooks/workable/")
    assert stored["subscriptions"] == ["sub-1"]
    # Another company's interview, or a job or stage Workable doesn't have, isn't linked.
    other = {**body, "interview_id": str(THEIR_INTERVIEW)}
    unknown = {**body, "stage_id": "offer", "interview_id": str(INTERVIEW_ID)}

    assert client.post(f"/links?company_id={COMPANY_ID}", json=other).status_code == 404
    assert client.post(f"/links?company_id={COMPANY_ID}", json=unknown).status_code == 404
    assert len(stored["links"]) == 1


def test_linked_jobs_show_their_interviews_titles_from_companies(client, stored, monkeypatch):
    from ats.models.ats import AtsJobLink

    gone = uuid.uuid4()
    found = [
        (
            AtsJobLink(id=uuid.uuid4(), interview_id=INTERVIEW_ID, job_name="A", stage_name="S"),
            "workable",
        ),
        (
            AtsJobLink(id=uuid.uuid4(), interview_id=gone, job_name="B", stage_name="S"),
            "greenhouse",
        ),
    ]

    async def links(company_id):
        return found

    monkeypatch.setattr(ats_links, "links", links)
    sign_in("vic")

    titles = [
        item["interview_title"] for item in client.get(f"/links?company_id={COMPANY_ID}").json()
    ]

    assert titles == ["Accountant", None]


@pytest.mark.parametrize("provider", ["workable", "teamtailor", "breezy"])
def test_a_job_deleted_in_the_ats_isnt_linked_and_says_so(
    client, stored, key, monkeypatch, provider
):
    from ats.services import ats as integrations

    async def credentials(connection):
        return {
            "subdomain": "acme",
            "token": "good",
            "host": "https://api.teamtailor.com",
            "key": "k",
            "company": "c",
        }

    def gone(request):
        return httpx.Response(404)

    api = httpx.AsyncClient(transport=httpx.MockTransport(gone))
    sign_in("ann")
    connect(client)
    stored["connection"].provider = provider
    # The ATS's own client, answering 404 for the deleted job.
    monkeypatch.setattr(workable, "job", WORKABLE_JOB)
    monkeypatch.setattr(integrations, "credentials", credentials)
    monkeypatch.setattr(http, "get_client", lambda: api)
    body = {"provider": provider, "job_id": "A1", "stage_id": "assessment"}

    response = client.post(
        f"/links?company_id={COMPANY_ID}", json={**body, "interview_id": str(INTERVIEW_ID)}
    )
    names = {"workable": "Workable", "teamtailor": "Teamtailor", "breezy": "Breezy HR"}

    assert response.status_code == 404
    assert response.json()["detail"] == f"That job or stage isn't in {names[provider]}"
    assert stored["links"] == []
