"""A brand's font splits in two, as the site has: one for titles (brand_heading_font) and one
for the text (brand_text_font). A saved font becomes both; prepza's pair (poppins_geist) becomes
Poppins titles over Geist text. brand_font and its CHECK go. The new CHECKs are added NOT VALID
and validated in their own transaction, which reads the rows without blocking writes

Revision ID: 0067
Revises: 0066
Create Date: 2026-10-29
"""

import sqlalchemy as sa
from alembic import op

revision = "0067"
down_revision = "0066"
branch_labels = None
depends_on = None

FONTS = "'poppins', 'geist', 'inter', 'roboto', 'open_sans', 'lato', 'montserrat', 'nunito', 'raleway', 'work_sans', 'source_sans_3', 'noto_sans', 'pt_sans', 'ubuntu', 'rubik', 'manrope', 'dm_sans', 'ibm_plex_sans', 'mulish', 'fira_sans', 'plus_jakarta_sans', 'outfit', 'merriweather', 'lora', 'playfair_display'"
OLD_FONTS = "'poppins_geist', 'inter', 'roboto', 'open_sans', 'lato', 'montserrat', 'nunito', 'raleway', 'work_sans', 'source_sans_3', 'noto_sans', 'pt_sans', 'ubuntu', 'rubik', 'manrope', 'dm_sans', 'ibm_plex_sans', 'mulish', 'fira_sans', 'plus_jakarta_sans', 'outfit', 'merriweather', 'lora', 'playfair_display'"
CHECKS = ("brand_heading_font", "brand_text_font")


def upgrade() -> None:
    op.add_column("companies", sa.Column("brand_heading_font", sa.String(32)))
    op.add_column("companies", sa.Column("brand_text_font", sa.String(32)))
    # migration-check: one row per company, a few thousand at most
    op.execute(
        "UPDATE companies SET"
        " brand_heading_font = CASE WHEN brand_font = 'poppins_geist' THEN 'poppins'"
        " ELSE brand_font END,"
        " brand_text_font = CASE WHEN brand_font = 'poppins_geist' THEN 'geist'"
        " ELSE brand_font END"
        " WHERE brand_font IS NOT NULL"
    )
    op.execute("ALTER TABLE companies DROP CONSTRAINT ck_companies_brand_font")
    op.drop_column("companies", "brand_font")

    for column in CHECKS:
        op.execute(
            f"ALTER TABLE companies ADD CONSTRAINT ck_companies_{column}"
            f" CHECK ({column} IN ({FONTS})) NOT VALID"
        )

    with op.get_context().autocommit_block():
        for column in CHECKS:
            op.execute(f"ALTER TABLE companies VALIDATE CONSTRAINT ck_companies_{column}")


def downgrade() -> None:
    op.add_column("companies", sa.Column("brand_font", sa.String(32)))
    op.execute(
        "UPDATE companies SET brand_font = CASE WHEN brand_text_font = 'geist'"
        " THEN 'poppins_geist' ELSE brand_text_font END"
        " WHERE brand_text_font IS NOT NULL"
    )
    op.execute(
        "ALTER TABLE companies ADD CONSTRAINT ck_companies_brand_font"
        f" CHECK (brand_font IN ({OLD_FONTS})) NOT VALID"
    )

    for column in CHECKS:
        op.execute(f"ALTER TABLE companies DROP CONSTRAINT ck_companies_{column}")
        op.drop_column("companies", column)
