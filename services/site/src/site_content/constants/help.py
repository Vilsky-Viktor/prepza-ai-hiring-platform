import re
from enum import StrEnum
from pathlib import Path


# Legal documents the help routes serve, by the path they're asked for under.
class LegalDocument(StrEnum):
    TERMS = "terms"
    PRIVACY = "privacy"
    DPA = "dpa"


# How long billing's prices are kept for the FAQ and the help chat's knowledge before they're
# asked again.
CATALOG_KEY = "billing-catalog"
CATALOG_CACHE_SECONDS = 5 * 60

# The FAQ's example of a small company's hiring, in candidates a month, priced over a year.
FAQ_EXAMPLE_CANDIDATES = 5
# How long the platform guide (GET /help/guide, and the help chat's knowledge) is kept, per
# language and country, before it's built again.
GUIDE_CACHE_SECONDS = CATALOG_CACHE_SECONDS
# The FAQ names today's prices; without them (billing not answering) it isn't served.
PRICES_UNAVAILABLE = "Prices aren't available right now. Please try again in a minute."

# A page's guide asked for by a key that isn't a page's (GET /help/pages/{key}).
NO_SUCH_PAGE = "There's no guide for this page."
# The longest page key a request may name.
MAX_PAGE_KEY_LENGTH = 40

# The site's guide articles, where the site keeps them: English at guides/<slug>.md, each
# translation at <language>/guides/<slug>.md, Markdown with "key: value" frontmatter. The image
# and the local stack put frontend/content at the same place relative to the code (repo layout).
ARTICLES_ROOT = Path(__file__).resolve().parents[5] / "frontend" / "content"
GUIDES_FOLDER = "guides"
# A slug as the files are named; anything else is never read.
GUIDE_SLUG = re.compile(r"^[a-z0-9-]+$")
# Where the site shows a guide.
GUIDE_PATH = "/guides/{slug}"
NO_SUCH_GUIDE = "There's no such guide."
MAX_GUIDE_SLUG_LENGTH = 80
# The guide article a page's guide points to, by the page's key: its help shows it as a link.
PAGE_ARTICLES = {
    "interviewSettings": "skills-test-timing-and-extra-time",
    "candidate": "skills-test-timing-and-extra-time",
}
