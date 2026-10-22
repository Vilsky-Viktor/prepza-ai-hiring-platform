import os
import uuid

from prepza_common.audit_actions import AuditAction, TargetKind
from prepza_common.lock_waits import hold_first_commit, race
from sqlalchemy import select

from app.constants.roles import EDITORS
from app.models.outbox import OutboxEvent
from app.storage import audit, companies, members
from app.storage.db import Session


def test_a_used_invite_link_still_finds_its_member_and_a_removed_admin_is_gone(run):
    """Reopening a used link says it was used (instead of "invalid"); joining again tells the
    owner nothing more."""

    async def scenario():
        company = await companies.create(f"Members {uuid.uuid4()}", "ann", "ann@example.com")
        bob = await members.add(company.id, "bob@example.com", "admin", {})
        cid = await members.add(company.id, "cid@example.com", "admin", {})
        await members.accept(bob, company, "bob")
        await members.accept(bob, company, "bob")
        reused = await members.get_by_token(bob.token)
        await members.remove(cid.id)
        left = await members.list_for_company(company.id, 0, 10)

        async with Session() as session:
            joined = (
                await session.scalars(
                    select(OutboxEvent).where(
                        OutboxEvent.data["key"].astext == f"member_joined:{bob.id}"
                    )
                )
            ).all()

        logged = await audit.list_for_company(company.id, 0, 10)
        await companies.delete(company.id)

        return reused, left, joined, bob.token, logged, bob.id

    reused, left, joined, token, logged, bob_id = run(scenario())

    assert reused is not None and reused[0].user_id == "bob"
    # Joining is logged once, with the join itself, however often the link is opened.
    assert [(row.user_id, row.action, row.target_id, row.target_kind) for row in logged] == [
        ("bob", AuditAction.MEMBER_JOINED, bob_id, TargetKind.MEMBER)
    ]
    assert [(row.invited_email, row.user_id, row.token) for row in left] == [
        ("ann@example.com", "ann", None),
        ("bob@example.com", "bob", token),
    ]
    assert len(joined) == 1


def test_a_viewer_keeps_their_role_on_joining_and_the_owner_changes_it(run):
    uid = f"bob-{uuid.uuid4()}"

    async def scenario():
        company = await companies.create(f"Viewers {uuid.uuid4()}", "ann", "ann@example.com")
        bob = await members.add(company.id, "bob@example.com", "viewer", {})
        # An id of its own: other tests' companies have a "bob" too.
        await members.accept(bob, company, uid)
        joined = await members.list_for_company(company.id, 0, 10)
        top_up_before = await companies.list_for_user(uid, 0, 10, EDITORS)
        await members.set_role(bob.id, "admin")
        changed = await members.list_for_company(company.id, 0, 10)
        top_up_after = await companies.list_for_user(uid, 0, 10, EDITORS)
        await companies.delete(company.id)

        return joined, changed, top_up_before, [item.id for item in top_up_after], company.id

    joined, changed, top_up_before, top_up_after, company_id = run(scenario())

    assert [(row.user_id, row.role) for row in joined] == [("ann", "owner"), (uid, "viewer")]
    assert [(row.user_id, row.role) for row in changed] == [("ann", "owner"), (uid, "admin")]
    # Only an owner or admin tops the company up.
    assert top_up_before == []
    assert top_up_after == [company_id]


def test_an_invite_saves_its_email_with_the_join_link(run):
    async def scenario():
        company = await companies.create(f"Emails {uuid.uuid4()}", "ann", "ann@example.com")
        dan = await members.add(company.id, "Dan@example.com", "viewer", {"company": "Acme"})

        async with Session() as session:
            sent = list(
                await session.scalars(
                    select(OutboxEvent.data).where(
                        OutboxEvent.event_type == "member.invited",
                        OutboxEvent.data["token"].astext == dan.token,
                    )
                )
            )

        await companies.delete(company.id)

        return dan, sent

    dan, sent = run(scenario())

    assert sent == [
        {"company": "Acme", "email": "dan@example.com", "token": dan.token, "role": "viewer"}
    ]


def test_the_owner_hears_once_that_a_member_joined(run):
    async def scenario():
        company = await companies.create(f"Joined {uuid.uuid4()}", "ann", "ann@example.com")
        dan = await members.add(company.id, "dan@example.com", "viewer", {})
        await members.accept(dan, company, "dan")
        # Accepting again (a retried request) changes nothing.
        await members.accept(dan, company, "dan")

        async with Session() as session:
            sent = list(
                await session.scalars(
                    select(OutboxEvent.data).where(
                        OutboxEvent.event_type == "notification.requested",
                        OutboxEvent.data["kind"].astext == "member_joined",
                        OutboxEvent.data["link"].astext == f"/companies/{company.id}/members",
                    )
                )
            )

        await companies.delete(company.id)

        return company, dan, sent

    company, dan, sent = run(scenario())

    assert sent == [
        {
            "recipient": "user",
            "recipient_id": "ann",
            "kind": "member_joined",
            "link": f"/companies/{company.id}/members",
            "data": {"email": "dan@example.com", "name": company.name, "role": "viewer"},
            "key": f"member_joined:{dan.id}",
        }
    ]


def test_two_joins_at_once_tell_the_owner_once_and_a_removed_invite_joins_no_one(run, monkeypatch):
    async def scenario():
        company = await companies.create(f"Members {uuid.uuid4()}", "ann", "ann@example.com")
        bob = await members.add(company.id, "bob@example.com", "admin", {})
        cid = await members.add(company.id, "cid@example.com", "admin", {})
        twice = await members.add(company.id, "cid@example.com", "admin", {})
        held = hold_first_commit(monkeypatch, members)
        both = await race(
            os.environ["DATABASE_URL"],
            held,
            members.accept(bob, company, "bob"),
            members.accept(bob, company, "bob"),
        )
        await members.remove(cid.id)
        removed = await members.accept(cid, company, "cid")

        async with Session() as session:
            joined = (
                await session.scalars(
                    select(OutboxEvent).where(
                        OutboxEvent.data["key"].astext == f"member_joined:{bob.id}"
                    )
                )
            ).all()

        await companies.delete(company.id)

        return twice, both, removed, len(joined)

    assert run(scenario()) == (None, (True, True), False, 1)


def test_the_database_refuses_a_second_owner(run):
    from sqlalchemy.exc import IntegrityError

    from app.models.companies import Member

    async def scenario():
        company = await companies.create(f"Owners {uuid.uuid4()}", "ann", "ann@example.com")

        async with Session() as session:
            session.add(
                Member(
                    company_id=company.id,
                    user_id="bob",
                    invited_email="bob@example.com",
                    role="owner",
                )
            )

            try:
                await session.commit()
            except IntegrityError as error:
                return error.orig.diag.constraint_name

    assert run(scenario()) == "uq_members_one_owner"


def test_two_invites_at_once_cant_both_take_the_last_pending_place(run, monkeypatch):
    from app.core.exceptions import OverLimit

    async def scenario():
        company = await companies.create(f"Pending {uuid.uuid4()}", "ann", "ann@example.com")
        held = hold_first_commit(monkeypatch, members)
        outcomes = await race(
            os.environ["DATABASE_URL"],
            held,
            *(
                members.add(company.id, f"{name}@example.com", "viewer", {}, most=1)
                for name in ("bob", "cid")
            ),
        )

        return [type(outcome).__name__ for outcome in outcomes]

    assert run(scenario()) == ["Member", OverLimit.__name__]


def test_two_companies_at_once_cant_both_take_the_last_owned_place(run, monkeypatch):
    from app.core.exceptions import OverLimit

    owner = f"owner-{uuid.uuid4()}"

    async def scenario():
        held = hold_first_commit(monkeypatch, companies)
        outcomes = await race(
            os.environ["DATABASE_URL"],
            held,
            *(
                companies.create(f"{name} {uuid.uuid4()}", owner, "o@example.com", most=1)
                for name in ("First", "Second")
            ),
        )

        return [type(outcome).__name__ for outcome in outcomes]

    assert run(scenario()) == ["Company", OverLimit.__name__]
