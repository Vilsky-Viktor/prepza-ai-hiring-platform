# The invite emails' texts in every supported language (prepza_common.config.constants.LANGUAGES), one
# module each in languages/. None of them needs the inviter's gender: past-tense or gendered
# verbs are avoided.
from importlib import import_module

from prepza_common.config.constants import LANGUAGES

EMAILS = {
    code: import_module(f"notifications.templates.languages.{code}").TEXTS for code in LANGUAGES
}
