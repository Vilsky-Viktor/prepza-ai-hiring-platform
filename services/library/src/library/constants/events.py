# One answer to one question, from rounds; added to the question's statistics.
ANSWER_RECORDED = "answer.recorded"
# A candidate finished one topic in rounds: its score and each shown question's result.
SESSION_SCORED = "session.scored"
# Processed events are remembered this long: past Pub/Sub's 7 days of redeliveries.
PROCESSED_EVENT_DAYS = 8
# Companies deleted guest invites: each guest's sign-in and what library kept under it go.
GUESTS_DELETED = "guests.deleted"
# A flagged bank question was fixed: its copies in companies' tests that still hold its old
# content get the new one, a batch at a time (library's own event, services/copy_fixes.py).
QUESTION_FIXED = "question.fixed"
