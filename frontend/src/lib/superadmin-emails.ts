import { apiFetch } from "@/lib/api"
import { DIGEST_KINDS, OTHER_EMAILS } from "@/constants/emails"
import type { EmailChanges, EmailPreferences } from "@/types/emails"
import type { CandidateOptOuts } from "@/types/superadmin"

const OPT_OUTS = "/notifications/superadmin/candidate-opt-outs"

/** The companies that invited an address, and what it stopped. The address goes in the body,
 * never a page or API address, which logs record. */
export function companyEmails(email: string) {
  return apiFetch<CandidateOptOuts>(`${OPT_OUTS}/lookup`, {
    method: "POST",
    body: JSON.stringify({ email }),
  })
}

/** Every setting the Settings page shows, turned off. */
export function allOptionalEmailsOff(): EmailChanges {
  return Object.fromEntries(
    [...DIGEST_KINDS, ...OTHER_EMAILS].map((setting) => [setting, false])
  )
}

/** Saves a user's email settings on their behalf; the API logs them as the superadmin's. */
export function saveForUser(userId: string, changes: EmailChanges) {
  return apiFetch<EmailPreferences>(
    `/library/superadmin/emails/${userId}/preferences`,
    { method: "PUT", body: JSON.stringify({ changes }) }
  )
}

/** Stops a company's emails to the address, or lets them through again; the API answers with
 * the companies as the lookup does. */
export function setCompanyEmails(
  email: string,
  companyId: string,
  stopped: boolean
) {
  return apiFetch<CandidateOptOuts>(OPT_OUTS, {
    method: "PUT",
    body: JSON.stringify({ email, company_id: companyId, stopped }),
  })
}
