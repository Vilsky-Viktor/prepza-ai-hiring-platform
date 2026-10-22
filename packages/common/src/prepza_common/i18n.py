from fastapi import FastAPI, Request
from fastapi import HTTPException as RaisedHTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prepza_common.constants import DEFAULT_LANGUAGE, LANGUAGES
from prepza_common.translations import TRANSLATIONS
from starlette.exceptions import HTTPException

# Pydantic's prefix on messages raised from a validator.
VALUE_ERROR = "Value error, "
# Traditional Chinese (Taiwan's, Hong Kong's, Macau's, or the Hant script): never given the
# Simplified Chinese that "zh" is.
TRADITIONAL_CHINESE = ("zh-tw", "zh-hk", "zh-mo", "zh-hant")


def language_of(accept_language: str) -> str:
    """The interface language in an Accept-Language header: its first tag, without its region
    ("fil-PH" is Filipino, "pt-BR" Portuguese); Traditional Chinese gets the default."""
    tag = accept_language.split(",")[0].split(";")[0].strip().lower()

    if tag.startswith(TRADITIONAL_CHINESE):
        return DEFAULT_LANGUAGE

    value = tag.split("-")[0]

    return value if value in LANGUAGES else DEFAULT_LANGUAGE


def request_language(request: Request) -> str:
    """The interface language, which the frontend sends as Accept-Language."""
    return language_of(request.headers.get("accept-language", ""))


def translate(text: str, language: str) -> str:
    return TRANSLATIONS.get(language, {}).get(text, text)


class CodedError(RaisedHTTPException):
    """A refusal with a stable, machine-readable `code` beside its translated `detail`, for
    clients (the public API's) that branch on it rather than on the text."""

    def __init__(
        self, status_code: int, detail: str, code: str, *, headers: dict[str, str] | None = None
    ):
        super().__init__(status_code, detail, headers=headers)
        self.code = code


class TemplateError(RaisedHTTPException):
    """An error whose message carries values, such as a limit's current number: `template` is
    translated first, then filled in with `values`; `code` as in CodedError. FastAPI's
    HTTPException, so code that lets those through (rate_limit.hit_or_skip) lets this one
    through too."""

    def __init__(
        self,
        status_code: int,
        template: str,
        *,
        headers: dict[str, str] | None = None,
        code: str | None = None,
        **values: object,
    ):
        super().__init__(status_code, template.format(**values), headers=headers)
        self.template = template
        self.values = values
        self.code = code


def add_localized_errors(app: FastAPI, codes: dict[int, str] | None = None) -> None:
    """Error messages in the language of the interface that asked, with the refusal's `code` when
    it has one (CodedError, TemplateError). With `codes` (a status to its code), every refusal
    carries one: its own, or its status's; validation errors the code of 422, beside the list
    that names each bad field."""
    codes = codes or {}

    async def http_error(request: Request, error: HTTPException):
        if isinstance(error, TemplateError):
            language = request_language(request)
            error.detail = translate(error.template, language).format(**error.values)
        elif isinstance(error.detail, str):
            error.detail = translate(error.detail, request_language(request))

        code = getattr(error, "code", None) or codes.get(error.status_code)

        if code is None:
            return await http_exception_handler(request, error)

        return JSONResponse(
            {"detail": error.detail, "code": code},
            status_code=error.status_code,
            headers=error.headers,
        )

    async def validation_error(request: Request, error: RequestValidationError):
        language = request_language(request)
        errors = error.errors()

        for item in errors:
            message = item.get("msg", "")

            if message.startswith(VALUE_ERROR):
                item["msg"] = VALUE_ERROR + translate(message.removeprefix(VALUE_ERROR), language)

        if 422 not in codes:
            return await request_validation_exception_handler(request, error)

        return JSONResponse(
            {"detail": jsonable_encoder(errors), "code": codes[422]}, status_code=422
        )

    app.add_exception_handler(HTTPException, http_error)
    app.add_exception_handler(RequestValidationError, validation_error)
