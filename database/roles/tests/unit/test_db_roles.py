"""The job reads each service's login from its DATABASE_URL_<NAME>, and refuses to run when a
service would share the admin's user or has none."""

import pytest

import db_roles

ADMIN = "postgresql://testee:admin@db:5432/postgres"


def test_reads_each_services_database_user_and_password():
    environ = {
        "DATABASE_URL_SITE": "postgresql://site:p%40ss@db:5432/site",
        "DATABASE_URL_API": "postgresql://api:secret@/api?host=/cloudsql/x",
        "ADMIN_DATABASE_URL": ADMIN,
        "OTHER": "postgresql://other:x@db/other",
    }

    assert db_roles.service_logins(environ) == [
        ("api", "api", "secret"),
        ("site", "site", "p@ss"),
    ]


@pytest.mark.parametrize(
    "services",
    [
        {},
        {"DATABASE_URL_API": "postgresql://testee:admin@db:5432/api"},
        {"DATABASE_URL_API": "postgresql://db:5432/api"},
    ],
)
def test_refuses_without_a_user_of_its_own_for_each_service(monkeypatch, services):
    monkeypatch.setattr(db_roles.os, "environ", {"ADMIN_DATABASE_URL": ADMIN, **services})

    with pytest.raises(SystemExit, match="its own user"):
        db_roles.main()
