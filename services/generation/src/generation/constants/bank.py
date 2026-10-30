import re

# The daily bank filter (services/bank_filter.py): companies' questions library offers, a page
# at a time, each checked by code and then by the model, a few at once.
BANK_FILTER_PAGE = 50
BANK_FILTER_AT_ONCE = 4
# Checks one run makes at most; the rest wait for the next day.
MAX_BANK_CHECKS = 1000
# One run at a time; the lock outlasts the worker's 30-minute request timeout.
BANK_FILTER_LOCK_KEY = "lock:bank-filter"
BANK_FILTER_LOCK_SECONDS = 30 * 60
# Contact details a general question never needs: an email address or a web address. Checked by
# code before the model, so one never reaches the bank whatever the model says.
CONTACT_DETAILS = (
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    re.compile(r"\bhttps?://|\bwww\.", re.IGNORECASE),
)
