from api.constants.docs_api import API_TAB
from api.constants.docs_sdk import SDK_TAB
from api.constants.docs_webhooks import WEBHOOKS_TAB

# The public API's description: its reference's API, web hooks and SDK tabs, each under its
# "# " title (the developer docs page splits it there; objects are the fourth tab).
API_TITLE = "testee API"
API_VERSION = "1"
API_DESCRIPTION = API_TAB + WEBHOOKS_TAB + SDK_TAB
