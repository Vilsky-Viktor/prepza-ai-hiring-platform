import uuid

from prepza_common.notifications import NotificationKind, Recipient, notification

from app.storage import notifications
from tests.integration.factories import api, company, finished, push


def test_a_deleted_companys_notifications_go_and_none_come_after(run):
    company_id, other_id = company(), company()
    deleted = push("company.deleted", {"company_id": company_id}, message_id="m-del")

    async def scenario():
        await notifications.add(str(uuid.uuid4()), finished(company_id, email="a@x.com"))
        await notifications.add(str(uuid.uuid4()), finished(other_id, email="b@x.com"))

        async with api() as client:
            # Pub/Sub may deliver it twice.
            codes = [(await client.post("/internal/events", json=deleted)).status_code]
            codes.append((await client.post("/internal/events", json=deleted)).status_code)

        # A notification that was on its way when the company went.
        late = notification(
            Recipient.COMPANY, company_id, NotificationKind.INTERVIEW_READY, "/x", title="T"
        )
        stored_late = await notifications.add(str(uuid.uuid4()), late)
        left = await notifications.latest([(Recipient.COMPANY, company_id)], limit=None)
        others = await notifications.latest([(Recipient.COMPANY, other_id)], limit=None)

        return codes, stored_late, left, others

    codes, stored_late, left, others = run(scenario())

    assert codes == [204, 204]
    assert stored_late is False
    assert left == []
    # Another company keeps its own.
    assert [item.data["email"] for item in others] == ["b@x.com"]


def test_an_erased_candidate_leaves_only_that_companys_bell_and_a_deleted_account_every_one(run):
    company_id, other_id = company(), company()
    removed = push(
        "candidate.removed",
        {"company_id": company_id, "interview_id": str(uuid.uuid4()), "email": "gone@x.com"},
        message_id=f"m-{uuid.uuid4()}",
    )

    async def latest(recipient_id):
        found = await notifications.latest([(Recipient.COMPANY, recipient_id)], limit=None)

        return [item.data["email"] for item in found]

    async def scenario():
        for recipient_id, email in [
            (company_id, "gone@x.com"),
            (company_id, "stays@x.com"),
            (other_id, "gone@x.com"),
        ]:
            await notifications.add(str(uuid.uuid4()), finished(recipient_id, email=email))

        async with api() as client:
            code = (await client.post("/internal/events", json=removed)).status_code

        after_erasure = (await latest(company_id), await latest(other_id))
        # The candidate deletes their prepza account: every company forgets them.
        await notifications.remove_candidate("Gone@x.com")

        return code, after_erasure, await latest(other_id)

    code, (own, other), other_after_account = run(scenario())

    assert code == 204
    assert own == ["stays@x.com"]
    assert other == ["gone@x.com"]
    assert other_after_account == []


def test_a_deleted_account_takes_the_owners_notice_that_it_joined(run):
    owner = f"owner-{uuid.uuid4()}"

    def joined(email):
        return notification(
            Recipient.USER,
            owner,
            NotificationKind.MEMBER_JOINED,
            "/x",
            key=str(uuid.uuid4()),
            email=email,
            name="Acme",
            role="admin",
        )

    async def scenario():
        await notifications.add(str(uuid.uuid4()), joined("gone@x.com"))
        await notifications.add(str(uuid.uuid4()), joined("stays@x.com"))
        await notifications.remove_member("Gone@x.com")
        left = await notifications.latest([(Recipient.USER, owner)], limit=None)

        return [item.data["email"] for item in left]

    assert run(scenario()) == ["stays@x.com"]


def test_a_deleted_interviews_candidates_leave_the_bell_and_its_other_news_stays(run):
    company_id, interview_id = company(), str(uuid.uuid4())
    page = f"/companies/{company_id}/interviews/{interview_id}"
    other_page = f"/companies/{company_id}/interviews/{uuid.uuid4()}"
    deleted = push(
        "candidate.interview_deleted",
        {"company_id": company_id, "interview_id": interview_id},
        message_id=f"m-{uuid.uuid4()}",
    )

    def about(kind, link, **data):
        return notification(
            Recipient.COMPANY, company_id, kind, link, key=str(uuid.uuid4()), **data
        )

    async def scenario():
        for item in (
            about(NotificationKind.CANDIDATE_FINISHED, page, email="gone@x.com", grade=70),
            about(NotificationKind.INVITE_UNDELIVERED, page, email="lost@x.com"),
            about(NotificationKind.INTERVIEW_CANCELLED, page, title="Backend"),
            about(NotificationKind.CANDIDATE_FINISHED, other_page, email="stays@x.com"),
        ):
            await notifications.add(str(uuid.uuid4()), item)

        async with api() as client:
            codes = [
                (await client.post("/internal/events", json=deleted)).status_code for _ in "ab"
            ]

        left = await notifications.latest([(Recipient.COMPANY, company_id)], limit=None)

        return codes, sorted(item.data.get("email") or item.kind for item in left)

    codes, left = run(scenario())

    assert codes == [204, 204]
    assert left == ["interview_cancelled", "stays@x.com"]
