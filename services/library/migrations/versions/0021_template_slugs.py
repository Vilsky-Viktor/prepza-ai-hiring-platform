"""templates get readable slugs for their practice pages' URLs

Revision ID: 0021
Revises: 0020
Create Date: 2026-10-06
"""

import sqlalchemy as sa
from alembic import op

from library.helpers.slugs import slugify, unique_slug

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sets", sa.Column("slug", sa.String(120), nullable=True))
    op.create_unique_constraint("uq_sets_slug", "sets", ["slug"])

    # Oldest first, so the first template with a title keeps the plain slug.
    connection = op.get_bind()
    rows = connection.execute(
        sa.text("SELECT id, title FROM sets WHERE kind = 'template' ORDER BY created_at, id")
    )
    taken = set()

    for set_id, title in rows.all():
        slug = unique_slug(slugify(title), taken)
        taken.add(slug)
        connection.execute(
            sa.text("UPDATE sets SET slug = :slug WHERE id = :id"), {"slug": slug, "id": set_id}
        )


def downgrade() -> None:
    op.drop_constraint("uq_sets_slug", "sets", type_="unique")
    op.drop_column("sets", "slug")
