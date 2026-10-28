from typing import Protocol

from ats.constants.ats import AtsProvider
from ats.integrations import breezy, greenhouse, recruitee, teamtailor, workable


class AtsClient(Protocol):
    """What every ATS's client offers, each taking the connection's credentials as keyword
    arguments (Workable: subdomain and token; Greenhouse: client_id and client_secret). A
    refused key raises integrations.errors.KeyRejected; an ATS that fails, a 502. `KEYS` names
    the credentials it takes: a connection may keep others (a web hook's secret key)."""

    KEYS: tuple[str, ...]
    # What a 502 says when the ATS doesn't answer.
    UNAVAILABLE: str

    async def check(self, **credentials) -> None: ...

    async def jobs(self, **credentials) -> list[dict]: ...

    async def stages(self, job_id: str, **credentials) -> list[dict]: ...

    async def job(self, job_id: str, **credentials) -> dict: ...

    async def comment(
        self, candidate_id: str, member: str | None, text: str, **credentials
    ) -> None: ...


# The factory: each ATS and its client. A new ATS adds its client module here.
CLIENTS: dict[AtsProvider, AtsClient] = {
    AtsProvider.WORKABLE: workable,
    AtsProvider.GREENHOUSE: greenhouse,
    AtsProvider.TEAMTAILOR: teamtailor,
    AtsProvider.RECRUITEE: recruitee,
    AtsProvider.BREEZY: breezy,
}


def client(provider: str) -> AtsClient:
    return CLIENTS[AtsProvider(provider)]
