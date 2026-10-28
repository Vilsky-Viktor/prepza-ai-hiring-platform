# The pages the bell's notifications open.
INTERVIEW_LINK = "/companies/{company_id}/interviews/{interview_id}"
# A candidate's results, where Slack's "candidate finished" leads; the bell keeps the interview's
# page, which groups its candidates.
CANDIDATE_LINK = INTERVIEW_LINK + "/candidates/{invite_id}"
INTERVIEWS_LINK = "/companies/{company_id}/interviews"
MEMBERS_LINK = "/companies/{company_id}/members"
# notifications asks for at most this many companies' members in one call (its emails).
MAX_COMPANIES_PER_CALL = 1000
