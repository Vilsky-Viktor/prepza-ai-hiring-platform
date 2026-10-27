# The texts of the comment on a finished candidate in the ATS, in every supported language
# (prepza_common.config.constants.LANGUAGES), one module each in languages/.
from importlib import import_module

from prepza_common.config.constants import LANGUAGES

COMMENTS = {code: import_module(f"app.templates.languages.{code}").TEXTS for code in LANGUAGES}
