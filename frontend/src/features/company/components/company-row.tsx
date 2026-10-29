"use client"

import { MessagesSquareIcon, UserRoundIcon, UsersIcon } from "lucide-react"
import Link from "next/link"
import { useTranslations } from "next-intl"

import { IconStat } from "@/components/common/icon-stat"
import { VerifiedBadge } from "@/components/common/verified-badge"
import { CompanyLogo } from "@/components/common/company-logo"
import { PendingBadge } from "@/features/company/components/pending-badge"
import { RemoveCompany } from "@/features/company/components/remove-company"
import { INTEGRATION_LOGO, ROW_HOVER } from "@/config/lists"
import { firstGrapheme } from "@/lib/graphemes"
import { hasMessage } from "@/lib/messages"
import type { Company } from "@/types/company"

/** A company on the companies list, laid out like an interview's row: its logo tile (the
 * integrations rows' tile, the row's full height), its name with its badge and the user's role,
 * then how many interviews and members it has, and Remove. The whole row opens the company
 * (`href`). On phones the row starts with the name, and the counts go under it. */
export function CompanyRow({
  company,
  href,
  removable,
  onRemoved,
}: {
  company: Company
  href: string
  removable: boolean
  onRemoved: () => void
}) {
  const t = useTranslations("company")
  const roles = useTranslations("roles")

  return (
    // One hover surface: the link stretches over the whole row, Remove sits on top of it.
    <div
      className={`relative flex items-center gap-6 py-6 pe-3 max-sm:ps-6 ${ROW_HOVER}`}
    >
      <Link
        href={href}
        className="flex min-w-0 flex-1 items-center gap-4 self-stretch after:absolute after:inset-0"
      >
        {/* The logo whole, or its first letter; decorative, the name says it. Not on phones. */}
        <span
          aria-hidden
          data-testid="company-logo"
          className={`${INTEGRATION_LOGO} max-sm:hidden`}
        >
          {company.logo_url ? (
            <CompanyLogo
              url={company.logo_url}
              name=""
              className="size-full object-contain"
            />
          ) : (
            <span className="font-heading text-2xl font-medium text-muted-foreground uppercase">
              {firstGrapheme(company.name)}
            </span>
          )}
        </span>
        <span className="flex min-w-0 flex-1 items-center justify-between gap-4 max-sm:flex-col max-sm:items-start max-sm:gap-1">
          <span className="flex max-w-full min-w-0 items-center gap-2">
            <span className="truncate text-lg font-medium" title={company.name}>
              {company.name}
            </span>
            {company.verified_domain && (
              <VerifiedBadge
                domain={company.verified_domain}
                className="size-5"
              />
            )}
            {company.verification_status === "pending" && (
              <PendingBadge className="size-5" />
            )}
            {company.role === "owner" ? (
              <IconStat
                label={t("owner")}
                icon={<UserRoundIcon aria-hidden className="size-5" />}
              />
            ) : (
              <span className="shrink-0 text-sm text-muted-foreground">
                {hasMessage(roles, company.role)
                  ? roles(company.role)
                  : company.role}
              </span>
            )}
          </span>
          {/* The same 3rem columns on every row; the hover background only around the icon and
              count. */}
          <span className="flex shrink-0 items-center gap-6">
            <span className="flex shrink-0 sm:w-12 sm:justify-end">
              <IconStat
                label={t("interviewCount", { count: company.interview_count })}
                icon={<MessagesSquareIcon aria-hidden className="size-5" />}
                className="text-sm"
                data-testid="interview-count"
              >
                {company.interview_count}
              </IconStat>
            </span>
            <span className="flex shrink-0 sm:w-12 sm:justify-end">
              <IconStat
                label={t("memberCount", { count: company.member_count })}
                icon={<UsersIcon aria-hidden className="size-5" />}
                className="text-sm"
                data-testid="member-count"
              >
                {company.member_count}
              </IconStat>
            </span>
          </span>
        </span>
      </Link>
      {/* The same 3rem column on every row, so the counts line up. */}
      <div className="relative z-10 flex shrink-0">
        {removable ? (
          <RemoveCompany
            companyId={company.id}
            name={company.name}
            onRemoved={onRemoved}
          />
        ) : (
          <span className="size-12" />
        )}
      </div>
    </div>
  )
}
