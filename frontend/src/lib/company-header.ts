import type { Company } from "@/types/company"

/** A company page's CompanyHeader props from the company it read: the page adds its own
 * `companyId`, `current` tab and `action`. */
export function companyHeaderProps(company: Company) {
  return {
    suspended: company.suspended,
    name: company.name,
    logoUrl: company.logo_url ?? null,
    verifiedDomain: company.verified_domain ?? null,
    websiteDomain: company.website_domain ?? null,
    verificationStatus: company.verification_status,
    declineReason: company.decline_reason ?? null,
    canEdit: company.can_edit,
    canSeeActions: company.can_see_actions,
  }
}
