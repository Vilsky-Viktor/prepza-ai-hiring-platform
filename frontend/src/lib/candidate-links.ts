/** Where a candidate in a company's credit lists leads: the company's own candidate page, or
 * the admin zone's support page for the candidate. */
export type CandidateLinks = "company" | "support"

export function candidateHref(
  links: CandidateLinks,
  companyId: string,
  candidate: { interview_id: string; invite_id: string }
) {
  return links === "support"
    ? `/superadmin/support/candidates/${candidate.invite_id}`
    : `/companies/${companyId}/interviews/${candidate.interview_id}/candidates/${candidate.invite_id}`
}
