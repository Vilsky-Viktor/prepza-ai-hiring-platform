# AI usage and limit hits (the admin zone's AI costs tab): kept 13 months, for year-on-year
# comparison; limit changes 24 months.
USAGE_KEEP_DAYS = 395
CHANGES_KEEP_DAYS = 730
# The most expensive companies and users the tab lists, and the ones that hit each limit most.
TOP_SPENDERS = 20
TOP_HITTERS = 5
# A company's or user's AI spend on its support page, and a limit's hits in Controls, over the
# last this many days.
SPEND_DAYS = 30
HITS_DAYS = 7
# Limit changes listed in Controls, newest first.
CHANGES_SHOWN = 50
# Transcription is priced and counted by the minute; every other action by what it was for (a
# generation, a conversation's message, a question).
TRANSCRIPTION = "transcription"
UNKNOWN_LIMIT = "No such limit."
OUT_OF_BOUNDS = "Use a value from {lowest} to {highest}."
