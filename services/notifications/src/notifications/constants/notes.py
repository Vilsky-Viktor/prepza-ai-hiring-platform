# The team's notes on an interview (companies' note events): one bell item per member and
# interview while it's unread, every note posted to the company's Slack channel, and the day's
# notes in the activity digest.

# The interview's notes tab, which the bell, Slack and the digest open.
NOTES_LINK = "/companies/{company_id}/interviews/{interview_id}?tab=notes"
# A bell item keeps its latest notes (to take a deleted one back out, and to name their authors)
# and names the latest authors, newest first.
GROUP_NOTES_KEPT = 50
AUTHORS_SHOWN = 2
# Marks in the bell's received events (repositories/notifications.py Received): a deleted note,
# so a late or repeated event about it notifies nobody, and a deleted interview, whose notes went
# with it. Pruned with the other marks after KEEP_DAYS, long after Pub/Sub stops redelivering.
DELETED_NOTE_KEY = "note-deleted:{note_id}"
DELETED_INTERVIEW_KEY = "interview-deleted:{interview_id}"
# The digest's copy of each new note (pending_notes) outlasts its window (24 hours, read until the
# catch-up hour ends): kept this long after the note was written.
PENDING_NOTE_HOURS = 48
# The digest shows the latest notes of each interview as excerpts of at most this many characters.
DIGEST_EXCERPTS = 2
EXCERPT_CHARS = 160
# Slack takes at most 3,000 characters in a text block; a note is at most 2,000, but escaping can
# make it longer.
SLACK_TEXT_CHARS = 3000
