# The events ats acts on, from companies and billing.
# A candidate finished an interview: their results go back to the ATS that sent them.
CANDIDATE_FINISHED = "candidate.finished"
# An interview's questions are ready: candidates waiting for it are invited.
INTERVIEW_READY = "interview.ready"
# An interview was deleted: its linked jobs and candidates go.
INTERVIEW_DELETED = "interview.deleted"
# A company was deleted: its connections go, with their linked jobs and candidates.
COMPANY_DELETED = "company.deleted"
# Billing: a company got credits: candidates not invited for lack of credits are invited again.
CREDITS_ADDED = "credits.added"
# Only companies have wallets; the event names the owner's kind.
COMPANY_OWNER = "company"
# A company erased a candidate: its ATS record of them goes.
CANDIDATE_REMOVED = "candidate.removed"
# Its own: an ATS's web hook sent a new candidate, saved; inviting them runs from this event, so
# the web hook is answered at once (ats' `ats` family, infra/terraform/pubsub.tf).
ATS_CANDIDATE_ARRIVED = "ats.candidate_arrived"
