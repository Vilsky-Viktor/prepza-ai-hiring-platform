import json

from prepza_common.config.constants import LEGAL_VERSIONS

from rounds.helpers import legal


def test_every_current_text_is_kept_as_its_version():
    """A changed text needs a new version: python -m rounds.legal_archive keeps it."""
    for document, version in LEGAL_VERSIONS.items():
        kept = json.loads((legal.ARCHIVE / document / f"{version}.json").read_text())

        assert kept == legal.current(document), f"{document} changed: give it a new version"


def test_a_document_is_read_as_any_version_ever_published(client, tmp_path, monkeypatch):
    (tmp_path / "terms").mkdir()
    (tmp_path / "terms" / "2026-01-01.json").write_text(
        json.dumps({"intro": "Old terms.", "sections": []})
    )
    (tmp_path / "terms" / f"{LEGAL_VERSIONS['terms']}.json").write_text("{}")
    monkeypatch.setattr(legal, "ARCHIVE", tmp_path)

    now = client.get("/help/legal/terms").json()
    old = client.get("/help/legal/terms", params={"version": "2026-01-01"}).json()

    assert now["version"] == now["current"] == LEGAL_VERSIONS["terms"]
    assert now["versions"] == [LEGAL_VERSIONS["terms"], "2026-01-01"]
    assert (old["intro"], old["version"], old["current"]) == (
        "Old terms.",
        "2026-01-01",
        LEGAL_VERSIONS["terms"],
    )
    assert client.get("/help/legal/terms", params={"version": "1999-01-01"}).status_code == 404


def test_a_version_published_ahead_applies_from_its_day(tmp_path, monkeypatch):
    (tmp_path / "terms").mkdir()

    for name in ("2026-01-01", "2026-06-01", "2999-01-01"):
        (tmp_path / "terms" / f"{name}.json").write_text("{}")

    monkeypatch.setattr(legal, "ARCHIVE", tmp_path)

    assert legal.in_force("terms") == "2026-06-01"
    assert [
        legal.state(name, "2026-06-01") for name in ("2026-01-01", "2026-06-01", "2999-01-01")
    ] == [
        "replaced",
        "in_force",
        "upcoming",
    ]


def test_a_translated_version_is_served_in_the_language_asked_and_english_otherwise(
    client, tmp_path, monkeypatch
):
    version = LEGAL_VERSIONS["terms"]
    (tmp_path / "terms" / version).mkdir(parents=True)
    (tmp_path / "terms" / f"{version}.json").write_text("{}")
    (tmp_path / "terms" / version / "de.json").write_text(
        json.dumps({"intro": "Diese Bedingungen.", "sections": []})
    )
    monkeypatch.setattr(legal, "ARCHIVE", tmp_path)

    german = client.get("/help/legal/terms", params={"language": "de"}).json()
    french = client.get("/help/legal/terms", params={"language": "fr"}).json()

    assert (german["language"], german["intro"]) == ("de", "Diese Bedingungen.")
    # No French yet: the English text, said to be English.
    assert french["language"] == "en" and french["intro"] == legal.current("terms")["intro"]
    assert german["versions"] == [version]
