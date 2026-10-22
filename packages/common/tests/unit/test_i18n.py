from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from prepza_common.constants import RATE_LIMITED
from prepza_common.i18n import CodedError, TemplateError, add_localized_errors, language_of
from pydantic import BaseModel, field_validator


class Body(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def required(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Title is required")

        return value


app = FastAPI()
add_localized_errors(app)


@app.get("/limited")
def limited():
    raise HTTPException(429, RATE_LIMITED)


@app.get("/templated")
def templated():
    raise TemplateError(429, "At most {limit} an hour.", headers={"Retry-After": "30"}, limit=5)


@app.get("/unknown")
def unknown():
    raise HTTPException(409, "Something only English has")


@app.post("/titles")
def titles(body: Body):
    return body


@app.get("/coded")
def coded():
    raise CodedError(429, RATE_LIMITED, "rate_limited", headers={"Retry-After": "9"})


client = TestClient(app)

# An app whose every refusal carries a code: its own, or its status's.
coded_app = FastAPI()
add_localized_errors(coded_app, {404: "not_found", 422: "validation_failed"})


@coded_app.get("/missing")
def missing():
    raise HTTPException(404, "Interview not found")


@coded_app.get("/templated")
def coded_template():
    raise TemplateError(409, "At most {limit}.", code="quota_reached", limit=3)


@coded_app.post("/titles")
def coded_titles(body: Body):
    return body


coded_client = TestClient(coded_app)


def test_errors_come_in_the_interface_language():
    response = client.get("/limited", headers={"Accept-Language": "ru"})

    assert response.status_code == 429
    assert response.json() == {"detail": "Слишком много запросов. Попробуйте позже."}


def test_a_templated_error_keeps_its_values_and_headers():
    response = client.get("/templated")

    assert response.status_code == 429
    assert response.json() == {"detail": "At most 5 an hour."}
    assert response.headers["Retry-After"] == "30"


def test_english_and_unknown_languages_keep_the_message():
    assert client.get("/limited").json() == {"detail": RATE_LIMITED}
    assert client.get("/limited", headers={"Accept-Language": "sv-SE"}).json() == {
        "detail": RATE_LIMITED
    }


def test_a_message_without_a_translation_stays_english():
    response = client.get("/unknown", headers={"Accept-Language": "ru"})

    assert response.json() == {"detail": "Something only English has"}


def test_validator_messages_are_translated_too():
    response = client.post("/titles", json={"title": " "}, headers={"Accept-Language": "ru"})

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Value error, Нужно название"


def test_every_translation_language_is_offered():
    from prepza_common.constants import LANGUAGES
    from prepza_common.translations import TRANSLATIONS

    assert set(TRANSLATIONS) <= set(LANGUAGES)


def test_every_language_translates_every_message():
    from prepza_common.constants import DEFAULT_LANGUAGE, LANGUAGES
    from prepza_common.translations import TRANSLATIONS

    english = set(TRANSLATIONS["ru"])

    assert set(TRANSLATIONS) == set(LANGUAGES) - {DEFAULT_LANGUAGE}
    assert all(set(messages) == english for messages in TRANSLATIONS.values())


def test_a_three_letter_language_with_a_region_is_read_whole():
    response = client.get("/limited", headers={"Accept-Language": "fil-PH,fil;q=0.9"})

    assert response.json() == {"detail": "Masyadong maraming request. Subukang muli mamaya."}


def test_traditional_chinese_never_gets_simplified():
    assert language_of("zh-TW,zh;q=0.9") == "en"
    assert language_of("zh-Hant-HK") == "en"
    assert language_of("zh-HK") == "en"
    assert language_of("zh-CN") == "zh"
    assert language_of("zh") == "zh"


def test_raised_messages_finds_literals_and_constants_but_not_f_strings(tmp_path, monkeypatch):
    from prepza_common.translations import raised_messages

    package = tmp_path / "fakeapp"
    (package / "constants").mkdir(parents=True)
    (package / "__init__.py").write_text("")
    (package / "constants" / "__init__.py").write_text("")
    (package / "constants" / "texts.py").write_text('GONE = "It is gone"\n')
    (package / "routes.py").write_text(
        "from fastapi import HTTPException, status\n"
        "from fakeapp.constants import texts\n"
        "from fakeapp.constants.texts import GONE\n"
        "def a(): raise HTTPException(404, 'Not here')\n"
        "def b(): raise HTTPException(status.HTTP_410_GONE, GONE)\n"
        "def c(): raise HTTPException(410, detail=texts.GONE)\n"
        "def d(name): raise HTTPException(409, f'{name} is taken')\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    assert raised_messages(package) == {"Not here", "It is gone"}


def test_a_coded_refusal_carries_its_code_beside_the_translated_detail():
    response = client.get("/coded", headers={"Accept-Language": "ru"})

    assert response.json() == {
        "detail": "Слишком много запросов. Попробуйте позже.",
        "code": "rate_limited",
    }
    assert response.headers["Retry-After"] == "9"


def test_with_codes_every_refusal_has_one_and_validation_still_names_each_field():
    missing = coded_client.get("/missing")
    templated = coded_client.get("/templated")
    invalid = coded_client.post("/titles", json={"title": " "}, headers={"Accept-Language": "ru"})
    unknown_route = coded_client.get("/nowhere")

    assert missing.json() == {"detail": "Interview not found", "code": "not_found"}
    assert templated.json() == {"detail": "At most 3.", "code": "quota_reached"}
    assert invalid.json()["code"] == "validation_failed"
    assert [(item["loc"], item["msg"]) for item in invalid.json()["detail"]] == [
        (["body", "title"], "Value error, Нужно название")
    ]
    assert unknown_route.json()["code"] == "not_found"
