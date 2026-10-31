# The texts of the comment on a finished candidate in the ATS, in every supported language
# (testee_common.config.constants.LANGUAGES), one module each in languages/.
from importlib import import_module

from testee_common.config.constants import LANGUAGES

COMMENTS = {code: import_module(f"ats.templates.languages.{code}").TEXTS for code in LANGUAGES}
