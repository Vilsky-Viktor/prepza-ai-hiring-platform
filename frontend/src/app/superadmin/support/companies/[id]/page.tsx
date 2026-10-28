import Link from "next/link"
import { notFound } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { BackLink } from "@/components/common/back-link"
import { CreditHistory } from "@/features/billing/components/credit-history"
import { ReservedList } from "@/features/billing/components/reserved-list"
import { ActionList } from "@/features/company/components/action-list"
import { VerifiedBadge } from "@/components/common/verified-badge"
import { EntityId } from "@/components/common/entity-id"
import { LocalDate } from "@/components/common/local-date"
import { PageHeader } from "@/components/common/page-header"
import { AdjustCredits } from "@/features/superadmin/components/adjust-credits"
import {
  aiSpend,
  AiSpendLine,
} from "@/features/superadmin/components/ai-spend-line"
import { CompanyActions } from "@/features/superadmin/components/company-actions"
import { SupportInterviews } from "@/features/superadmin/components/support-lists"
import { TabNav } from "@/components/common/tab-nav"
import { Badge } from "@/components/ui/badge"
import { WrappedEmail } from "@/components/common/wrapped-email"
import { Dot } from "@/components/common/dot"
import { LIST_BOX, PAGE_SIZE, ROW_HOVER } from "@/config/lists"
import { hasMessage } from "@/lib/messages"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type {
  CompanyAction,
  CreditCandidate,
  CreditHistoryEntry,
  Interview,
} from "@/types/company"
import type { SupportCompany } from "@/types/superadmin"

export const generateMetadata = () => translatedTitle("superadmin", "zone")

/** A member's row: a link to their user page once they've joined (an account to look at). */
function MemberLink({
  userId,
  className,
  children,
}: {
  userId: string | null | undefined
  className: string
  children: React.ReactNode
}) {
  return userId ? (
    <Link
      href={`/superadmin/support/users/${userId}`}
      className={`${className} ${ROW_HOVER}`}
    >
      {children}
    </Link>
  ) : (
    <div className={className}>{children}</div>
  )
}

const TABS = ["money", "reserved", "interviews", "members", "audit"] as const

/** A company in the admin zone's support tab, to look into a complaint: its balance, where its
 * credits came from and went (with Paddle's transactions and invoices), the candidates holding
 * credits, its interviews, members and audit log; and what a superadmin can do about it. The
 * API answers superadmins only and logs each look. */
export default async function SupportCompanyPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>
  searchParams: Promise<{ tab?: string }>
}) {
  const { id } = await params
  const asked = (await searchParams).tab
  const tab = TABS.find((name) => name === asked) ?? "money"
  const t = await getTranslations("superadmin")
  const roles = await getTranslations("roles")
  const api = `/companies/superadmin/support/companies/${id}`
  // Only the open tab's first page, asked with the company and its AI spend.
  const first = <T,>(path: string) =>
    serverFetch<T[]>(`${api}/${path}?limit=${PAGE_SIZE}`)
  const [company, spend, history, reserved, interviews, audit] =
    await Promise.all([
      serverFetch<SupportCompany>(api),
      aiSpend(`company_id=${encodeURIComponent(id)}`),
      tab === "money" ? first<CreditHistoryEntry>("history") : null,
      tab === "reserved" ? first<CreditCandidate>("reserved") : null,
      tab === "interviews" ? first<Interview>("interviews") : null,
      tab === "audit" ? first<CompanyAction>("audit") : null,
    ])

  if (!company) {
    notFound()
  }

  const href = `/superadmin/support/companies/${id}`

  return (
    <main className="mx-auto max-w-page space-y-10 px-6 py-12">
      {/* The actions sit beside the name; on phones, on their own line under it. */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <PageHeader
          back={<BackLink href="/superadmin/support">{t("support")}</BackLink>}
          title={
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="font-heading text-3xl font-medium tracking-tight normal-case">
                  {company.name}
                </h1>
                {company.verified_domain && (
                  <VerifiedBadge
                    domain={company.verified_domain}
                    className="size-7"
                  />
                )}
                {company.suspended && (
                  <Badge
                    variant="destructive"
                    className="h-7 px-3 text-sm font-light"
                  >
                    {t("suspended")}
                  </Badge>
                )}
              </div>
              <p className="flex flex-wrap items-center gap-x-3 text-sm text-muted-foreground">
                <span>
                  {t("supportCreated")} <LocalDate iso={company.created_at} />
                </span>
                <EntityId id={company.id} />
              </p>
            </div>
          }
        />
        <div className="flex flex-wrap items-center gap-3 max-sm:basis-full max-sm:justify-center">
          <AdjustCredits companyId={company.id} name={company.name} />
          <CompanyActions company={company} />
        </div>
      </div>

      {/* One line on desktop; on phones, the held credits on a line of their own. */}
      <p className="text-lg">
        {t("supportAvailable", {
          available: company.balance - company.reserved,
        })}
        <Dot className="max-sm:hidden" />
        <span className="max-sm:block">
          {t("supportHeld", { reserved: company.reserved })}
        </span>
      </p>

      <AiSpendLine spend={spend} />

      <div className="space-y-6">
        <TabNav
          items={TABS.map((name) => ({
            id: name,
            href: name === "money" ? href : `${href}?tab=${name}`,
            label: t(`supportTabs.${name}`),
          }))}
          current={tab}
        />
        {history && (
          <CreditHistory
            companyId={id}
            initial={history}
            api={api}
            links="support"
          />
        )}
        {reserved && (
          <ReservedList
            companyId={id}
            initial={reserved}
            api={api}
            links="support"
          />
        )}
        {interviews && <SupportInterviews api={api} initial={interviews} />}
        {audit && <ActionList path={`${api}/audit`} initial={audit} />}
        {tab === "members" && (
          <ul className={LIST_BOX}>
            {company.members.map((member) => (
              // On desktop the role sits on the right; on phones, right after the status. A
              // member who joined opens their user page.
              <li key={member.email}>
                <MemberLink
                  userId={member.user_id}
                  className="flex items-center justify-between gap-4 p-6"
                >
                  <span className="min-w-0 space-y-1">
                    <span className="block text-lg font-medium">
                      <WrappedEmail email={member.email} />
                    </span>
                    <span className="flex items-center gap-3 text-sm text-muted-foreground">
                      {member.user_id
                        ? t("supportJoined")
                        : t("supportInvited")}
                      <Badge
                        variant="outline"
                        className="h-7 px-3 text-sm font-light sm:hidden"
                      >
                        {hasMessage(roles, member.role)
                          ? roles(member.role)
                          : member.role}
                      </Badge>
                    </span>
                  </span>
                  <Badge
                    variant="outline"
                    className="h-7 px-3 text-sm font-light max-sm:hidden"
                  >
                    {hasMessage(roles, member.role)
                      ? roles(member.role)
                      : member.role}
                  </Badge>
                </MemberLink>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  )
}
