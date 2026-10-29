# An interview's notes: plain text its team writes about the hiring round, never shown to
# candidates. A note is at most prepza_common's MAX_NOTE_LENGTH characters; the database holds
# the same bound (ck_interview_notes_text).
# The refusals, as the API and the tab show them.
NOTE_NOT_FOUND = "Note not found"
ONLY_AUTHOR_EDITS = "Only the note's author can edit it."
ONLY_AUTHOR_DELETES = "Only the note's author, the owner or an admin can delete it."
ONLY_EDITORS_PIN = "Only the owner or an admin can pin a note."
