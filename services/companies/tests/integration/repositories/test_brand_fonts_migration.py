import uuid

from alembic import command
from alembic.config import Config
from prepza_common.db.db import sqlalchemy_url
from sqlalchemy import create_engine, text

from companies.config import settings


def test_the_migration_gives_a_saved_font_to_both_the_titles_and_the_text():
    """Migration 0067: one font becomes both; prepza's pair becomes Poppins titles over Geist
    text; no font stays prepza's."""
    config = Config("alembic.ini")
    engine = create_engine(sqlalchemy_url(settings.database_url))
    fonts = {uuid.uuid4(): "inter", uuid.uuid4(): "poppins_geist", uuid.uuid4(): None}
    command.downgrade(config, "0066")

    try:
        with engine.begin() as connection:
            for company_id, font in fonts.items():
                connection.execute(
                    text(
                        "INSERT INTO companies (id, name, brand_font, logo_version, created_at) "
                        "VALUES (:id, :name, :font, 0, now())"
                    ),
                    {"id": company_id, "name": f"Acme {company_id}", "font": font},
                )
    finally:
        command.upgrade(config, "head")

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT id, brand_heading_font, brand_text_font FROM companies WHERE id = ANY(:ids)"
            ),
            {"ids": list(fonts)},
        ).all()

    found = {row[0]: (row[1], row[2]) for row in rows}
    inter, pair, none = fonts

    assert found == {inter: ("inter", "inter"), pair: ("poppins", "geist"), none: (None, None)}
