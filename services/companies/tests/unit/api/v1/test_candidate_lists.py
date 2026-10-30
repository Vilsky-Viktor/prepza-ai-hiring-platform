"""Names in a pasted or uploaded list of candidates, read on the backend."""

from types import SimpleNamespace

from companies.helpers.candidate_lists import read_list
from companies.services import candidate_invites
from tests.unit.api.v1.test_candidate_invites import INTERVIEW_ID, invite_setup

URL = f"/interviews/{INTERVIEW_ID}/candidates/bulk"


def test_name_then_email_and_email_then_name_lines_give_names():
    text = (
        "Maria Kowalska <Maria@Example.com>\n"
        '"Lee, Ann" <ann@example.com>,\n'
        "bob@example.com, Bob Stone\n"
        "cid@example.com;\tCid Moss\n"
        "plain@example.com\n"
        "a@example.com, b@example.com\n"
        "Contacts: c@example.com and more\n"
    )

    assert read_list(text)[0] == [
        ("maria@example.com", "Maria Kowalska"),
        ("ann@example.com", "Lee, Ann"),
        ("bob@example.com", "Bob Stone"),
        ("cid@example.com", "Cid Moss"),
        ("plain@example.com", None),
        ("a@example.com", None),
        ("b@example.com", None),
        ("c@example.com", None),
    ]


def test_a_csv_with_a_name_column_gives_names():
    text = "Email,Full Name,Role\nann@example.com,Ann Lee,Dev\nbob@example.com,,QA\n"

    assert read_list(text)[0] == [("ann@example.com", "Ann Lee"), ("bob@example.com", None)]


def test_a_csv_with_first_and_last_names_in_another_language_joins_them():
    text = "E-Mail;Vorname;Name\nmaria@example.com;Maria;Kowalska\n"

    assert read_list(text)[0] == [("maria@example.com", "Maria Kowalska")]


def test_localized_headers_count_too():
    text = "Имя,Фамилия,Email\nОльга,Петрова,olga@example.com\n"

    assert read_list(text)[0] == [("olga@example.com", "Ольга Петрова")]


def test_a_name_is_trimmed_cut_and_an_email_keeps_its_first_name():
    long = "x" * 300
    text = f"{long} <ann@example.com>\nann@example.com, Other"

    assert read_list(text)[0] == [("ann@example.com", "x" * 200)]


def test_the_list_invites_each_candidate_with_their_name(client, monkeypatch):
    invite_setup(monkeypatch)
    calls = []

    async def invite(interview, company, user, email, name=None, voice=None):
        calls.append((email, name))

        return SimpleNamespace(id=None)

    monkeypatch.setattr(candidate_invites, "invite", invite)
    text = "Ann Lee <ann@example.com>\nbob@example.com"

    assert client.post(URL, json={"text": text}).status_code == 200
    assert calls == [("ann@example.com", "Ann Lee"), ("bob@example.com", None)]


def test_the_forms_name_field_goes_with_its_one_email(client, monkeypatch):
    invite_setup(monkeypatch)
    calls = []

    async def invite(interview, company, user, email, name=None, voice=None):
        calls.append((email, name))

        return SimpleNamespace(id=None)

    monkeypatch.setattr(candidate_invites, "invite", invite)
    one = {"text": "ann@example.com", "name": "  Ann Lee "}
    many = {"text": "ann@example.com bob@example.com", "name": "Ann Lee"}

    assert client.post(URL, json=one).status_code == 200
    assert calls == [("ann@example.com", "Ann Lee")]
    assert client.post(URL, json=many).status_code == 422
