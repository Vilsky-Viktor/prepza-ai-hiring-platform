# The most questions a template's public sample shows (api/v1/templates.py).
SAMPLE_QUESTIONS = 5

# A slug is cut to this many characters before "-2", "-3"… is added; the column holds 120.
SLUG_LENGTH = 80

# The slug of a template whose title has no ASCII letters or digits.
FALLBACK_SLUG = "template"

# Slugs a template never gets: the words of the other /templates/<word> routes (api/v1/templates.py).
RESERVED_SLUGS = {"filters", "copyable"}

# Search engines index a template's public pages (its role test and practice pages) only with at
# least this many topics: a page about one or two topics is too thin to rank, and a demo or test
# template has one (helpers/templates.py).
MIN_INDEXABLE_TOPICS = 3
