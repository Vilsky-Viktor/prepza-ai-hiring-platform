CANDIDATE_INVITED = "candidate.invited"
# Someone started through a test's shareable link; notifications emails them their own invite
# link, to continue if they leave.
CANDIDATE_JOINED = "candidate.joined"
# The owner invited a member; notifications emails them the join link.
MEMBER_INVITED = "member.invited"
# A member emails a candidate's PDF report to someone; notifications sends it, attached.
REPORT_SHARED = "report.shared"
# A candidate who hasn't started is reminded once; the event carries what the invite did.
CANDIDATE_REMINDED = "candidate.reminded"
# A company interview's questions are saved; the event carries the set and its title.
GENERATION_COMPLETED = "generation.completed"
# An interview's generation failed; the interview shows it until a retry or its questions.
GENERATION_FAILED = "generation.failed"
# Generation cancelled an interview's topic review that waited too long; the interview goes too.
GENERATION_CANCELLED = "generation.cancelled"
# Rounds: every section of a candidate's interview is finished, with how many answers they
# picked; the company is charged for the candidate, or gets the credits back without one.
INTERVIEW_FINISHED = "interview.finished"
# A candidate's interview.finished was stored: their grade, whether they passed, and the
# interview's title; ats writes the result back to the ATS that sent them.
CANDIDATE_FINISHED = "candidate.finished"
# A generated interview got its questions; ats invites the candidates waiting for it, and the
# API's web hooks hear it.
INTERVIEW_READY = "interview.ready"
# A candidate started, their invite email bounced, or their invite expired: the API's web hooks
# hear it (repositories/candidate_events.py).
CANDIDATE_STARTED = "candidate.started"
CANDIDATE_UNDELIVERED = "candidate.undelivered"
CANDIDATE_EXPIRED = "candidate.expired"
# Processed events are remembered this long: past Pub/Sub's 7 days of redeliveries.
PROCESSED_EVENT_DAYS = 8
# A company erased a candidate (removed them, results included): other services forget them.
CANDIDATE_REMOVED = "candidate.removed"
# Guest invites (signed in by the company's own platform, no account of their own) were deleted:
# library deletes each guest's sign-in and what it stored under it (terms, ratings, reports).
GUESTS_DELETED = "guests.deleted"
# An interview was deleted, its candidates with it: notifications removes the company's
# notifications about them, and the api their results waiting to be sent to web hooks. Named
# under "candidate." so both get it within their subscriptions' filters (pubsub.tf).
CANDIDATE_INTERVIEW_DELETED = "candidate.interview_deleted"
