# The bias-audit export: one row per candidate who finished with a grade, for the company's
# independent auditor (NYC Local Law 144, DCWP rules 6 RCNY §5-300 to §5-304; the EEOC's
# four-fifths rule, 29 CFR §1607.4(D)). prepza never asks for, infers or stores protected
# characteristics: the company joins its own self-reported categories on the candidate's email,
# the one identifier it already holds, and the auditor works out the rates and impact ratios.
COLUMNS = (
    "candidate_id",
    "candidate_email",
    "interview_id",
    "interview_title",
    "finished_on",
    "grade",
    "pass_mark",
    "passed",
    "above_median",
)
# The file's name, with the day it was made (UTC).
FILE_NAME = "prepza-bias-audit-{day}.csv"
# A cell starting with one of these is read as a formula by spreadsheets: it's kept as text.
FORMULA_STARTS = ("=", "+", "-", "@", "\t", "\r")

NOT_OWNER = "Only the owner can export data for a bias audit"
