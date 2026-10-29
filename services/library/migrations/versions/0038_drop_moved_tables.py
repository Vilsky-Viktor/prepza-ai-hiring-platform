"""Drop the tables that moved out: users' email settings, their consent log, accepted terms and
recent erasures (the accounts service's now) and news posts with their translations (the site
service's). Their rows were copied there; nothing in library reads or writes them any more

Revision ID: 0038
Revises: 0037
Create Date: 2026-10-29
"""

from alembic import op

revision = "0038"
down_revision = "0037"
branch_labels = None
depends_on = None

# news_translations before news, which it refers to.
TABLES = (
    "email_preferences",
    "email_consents",
    "terms_acceptances",
    "erasures",
    "news_translations",
    "news",
)

# The tables as 0037 left them, empty, for the tests that migrate down past this one.
RECREATE = """
CREATE TABLE email_preferences (
    user_id varchar(128) PRIMARY KEY,
    candidate_finished boolean NOT NULL DEFAULT true,
    invite_undelivered boolean NOT NULL DEFAULT true,
    ats_not_invited boolean NOT NULL DEFAULT true,
    interview_ready boolean NOT NULL DEFAULT true,
    reminders boolean NOT NULL DEFAULT true,
    updates boolean NOT NULL DEFAULT false,
    promotions boolean NOT NULL DEFAULT false,
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE email_consents (
    id uuid PRIMARY KEY,
    user_id varchar(128) NOT NULL,
    setting varchar(32) NOT NULL,
    granted boolean NOT NULL,
    source varchar(16) NOT NULL,
    basis varchar(16) NOT NULL,
    text_version varchar(16) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    changed_by varchar(128),
    CONSTRAINT ck_email_consents_basis CHECK (basis IN ('choice', 'soft_opt_in')),
    CONSTRAINT ck_email_consents_setting CHECK (setting IN ('candidate_finished',
        'invite_undelivered', 'ats_not_invited', 'interview_ready', 'reminders', 'updates',
        'promotions')),
    CONSTRAINT ck_email_consents_source CHECK (source IN ('sign_in', 'settings', 'unsubscribe',
        'admin'))
);
CREATE INDEX ix_email_consents_user_id ON email_consents (user_id);
CREATE TABLE terms_acceptances (
    user_id varchar(128) NOT NULL,
    version varchar(10) NOT NULL,
    accepted_at timestamptz NOT NULL,
    PRIMARY KEY (user_id, version)
);
CREATE TABLE erasures (
    user_id varchar(128) PRIMARY KEY,
    email varchar(320) NOT NULL,
    erased_at timestamptz NOT NULL
);
CREATE INDEX ix_erasures_erased_at ON erasures (erased_at);
CREATE TABLE news (
    id uuid PRIMARY KEY,
    title varchar(120) NOT NULL,
    text text NOT NULL,
    published_on date NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_news_published_on_created_at ON news (published_on, created_at);
CREATE TABLE news_translations (
    news_id uuid NOT NULL REFERENCES news (id) ON DELETE CASCADE,
    language varchar(8) NOT NULL,
    title varchar(120) NOT NULL,
    text text NOT NULL,
    PRIMARY KEY (news_id, language)
);
"""


def upgrade() -> None:
    for table in TABLES:
        op.drop_table(table)


def downgrade() -> None:
    op.execute(RECREATE)
