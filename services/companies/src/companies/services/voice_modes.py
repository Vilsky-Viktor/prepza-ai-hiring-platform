"""Voice mode is only offered in the languages speech is reliable in (VOICE_LANGUAGES), for an
interview and for one candidate alike."""

from fastapi import status
from prepza_common.config.constants import VOICE_LANGUAGES
from prepza_common.i18n.i18n import CodedError

from companies.constants import error_codes
from companies.constants.interviews import VOICE_NOT_IN_LANGUAGE
from companies.models.interviews import Interview


def refuse_unspoken(interview: Interview, voice: bool | None) -> None:
    """Voice asked for an interview in a language voice mode doesn't speak: 422."""
    if voice and interview.language not in VOICE_LANGUAGES:
        raise CodedError(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            VOICE_NOT_IN_LANGUAGE,
            error_codes.VOICE_UNAVAILABLE,
        )
