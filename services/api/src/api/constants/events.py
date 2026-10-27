# The events api acts on, from companies.
# A candidate finished an interview, started it, their invite email bounced, or their invite
# expired: the company's web hooks hear it, with the interview and the candidate.
CANDIDATE_FINISHED = "candidate.finished"
CANDIDATE_STARTED = "candidate.started"
CANDIDATE_UNDELIVERED = "candidate.undelivered"
CANDIDATE_EXPIRED = "candidate.expired"
CANDIDATE_EVENTS = (CANDIDATE_FINISHED, CANDIDATE_STARTED, CANDIDATE_UNDELIVERED, CANDIDATE_EXPIRED)
# A company erased a candidate: their results waiting to be sent again to its web hooks go, and
# its web hooks hear which candidate it was.
CANDIDATE_REMOVED = "candidate.removed"
# A company deleted an interview, its candidates with it: their results waiting to be sent
# again to web hooks go.
CANDIDATE_INTERVIEW_DELETED = "candidate.interview_deleted"
# An interview's questions are ready: the company's web hooks hear it.
INTERVIEW_READY = "interview.ready"
# A company was deleted: its keys and web hooks go.
COMPANY_DELETED = "company.deleted"
# What a web hook's "send test event" sends.
TEST_EVENT = "test"
