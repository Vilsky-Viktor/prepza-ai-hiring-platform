"use client"

import { useTranslations } from "next-intl"
import { type ReactNode, useEffect, useState } from "react"

import { BackLink } from "@/components/common/back-link"
import {
  CompanyNav,
  type CompanyTab,
} from "@/features/company/components/company-nav"
import { LogoPicker } from "@/features/company/components/logo-picker"
import { PendingBadge } from "@/features/company/components/pending-badge"
import type { SideMenuItem } from "@/components/common/side-menu"
import { VerifiedBadge } from "@/components/common/verified-badge"
import { WarningCard } from "@/components/common/warning-card"
import { VerifyCompany } from "@/features/company/components/verify-company"
import { EditableTitle } from "@/components/common/editable-title"
import { EntityId } from "@/components/common/entity-id"
import { MAX_COMPANY_NAME_LENGTH } from "@/config/limits"
import { COMPANY_TAB_HELP } from "@/config/page-help"
import { apiFetch } from "@/lib/api"
import type { MenuCounts, VerificationStatus } from "@/types/company"

/** A company page: the way back, its logo, name and action, and its menu beside the page's
 * content (`children`, spaced by `className`), with the page's own pages under it (`sub`). */
export function CompanyHeader({
  suspended = false,
  companyId,
  name,
  logoUrl,
  verifiedDomain,
  websiteDomain,
  verificationStatus,
  declineReason,
  current,
  action,
  canEdit,
  canSeeActions = false,
  sub,
  currentSub,
  className,
  children,
}: {
  companyId: string
  name: string
  logoUrl: string | null
  // The verified domain (the badge); else the website, where its verification stands and why a
  // superadmin declined it.
  verifiedDomain: string | null
  websiteDomain: string | null
  verificationStatus: VerificationStatus
  declineReason: string | null
  current: CompanyTab
  action?: ReactNode
  // Owners and admins change the logo, name and website; viewers only see them.
  canEdit: boolean
  // The owner sees the action log's tab.
  canSeeActions?: boolean
  // A superadmin suspended the company: it can be read, not changed.
  suspended?: boolean
  // The open page's own pages, and the one open.
  sub?: SideMenuItem["sub"]
  currentSub?: string
  className?: string
  children: ReactNode
}) {
  const t = useTranslations("company")
  const verify = useTranslations("verify")
  // A rename sends a verified, pending or declined company for review again.
  const reviewed = ["approved", "pending", "declined"].includes(
    verificationStatus ?? ""
  )
  // The menu's counts, asked for once the page shows, so no page waits on them; none on failure.
  const [counts, setCounts] = useState<MenuCounts | null>(null)

  useEffect(() => {
    apiFetch<MenuCounts>(`/companies/companies/${companyId}/menu-counts`)
      .then(setCounts)
      .catch(() => setCounts(null))
  }, [companyId])

  return (
    <div className="space-y-4">
      {/* On narrower screens the back arrow and info button take their own line above the
          name, and on phones the action its own line below it, at full width. */}
      <div className="relative flex min-h-14 flex-wrap items-center">
        <BackLink
          href="/companies"
          help={COMPANY_TAB_HELP[current]}
          className="max-wide:basis-full"
        >
          {t("title")}
        </BackLink>
        {/* The logo candidates see; clicking it sets or changes it. */}
        <div className="me-4">
          <LogoPicker
            companyId={companyId}
            name={name}
            logoUrl={logoUrl}
            editable={canEdit}
          />
        </div>
        {/* Renamed in place, like a test's title; the name stays unique across testee. Then the
            verified badge, the pending one while a superadmin reviews it, or the way to verify;
            under the name, the id to quote when writing to testee about the company. The logo
            and the back arrow are centred on both lines. */}
        <div className="me-4 min-w-0 flex-1">
          <div className="flex min-w-0 items-center gap-3">
            <div className="min-w-0">
              <EditableTitle
                title={name}
                path={`/companies/companies/${companyId}/name`}
                maxLength={MAX_COMPANY_NAME_LENGTH}
                editable={canEdit}
                hint={reviewed ? verify("renameHint") : undefined}
              />
            </div>
            {verifiedDomain ? (
              <VerifiedBadge domain={verifiedDomain} className="size-7" />
            ) : canEdit ? (
              <VerifyCompany
                companyId={companyId}
                websiteDomain={websiteDomain}
                status={verificationStatus}
                declineReason={declineReason}
              />
            ) : (
              verificationStatus === "pending" && (
                <PendingBadge className="size-7" />
              )
            )}
          </div>
          <EntityId id={companyId} />
        </div>
        {action && (
          <div className="max-sm:my-4 max-sm:basis-full max-sm:*:w-full">
            {action}
          </div>
        )}
      </div>
      <CompanyNav
        companyId={companyId}
        current={current}
        canEdit={canEdit}
        canSeeActions={canSeeActions}
        counts={counts}
        sub={sub}
        currentSub={currentSub}
        className={className}
      >
        {suspended && (
          // Edge to edge on a phone.
          <WarningCard className="-mx-6 rounded-none sm:mx-0 sm:rounded-xl">
            {t("suspended")}
          </WarningCard>
        )}
        {children}
      </CompanyNav>
    </div>
  )
}
