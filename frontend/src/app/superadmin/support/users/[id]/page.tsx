import Link from "next/link"
import { notFound } from "next/navigation"
import { getLocale, getTranslations } from "next-intl/server"

import { BackLink } from "@/components/common/back-link"
import { EntityId } from "@/components/common/entity-id"
import { LocalDate } from "@/components/common/local-date"
import { PageHeader } from "@/components/common/page-header"
import { AccountEmails } from "@/features/superadmin/components/account-emails"
import { AddressSuppression } from "@/features/superadmin/components/address-suppression"
import { Badge } from "@/components/ui/badge"
import { WrappedEmail } from "@/components/common/wrapped-email"
import { Dot } from "@/components/common/dot"
import { LIST_BOX, ROW_HOVER } from "@/config/lists"
import { formatPrice } from "@/lib/format"
import { hasMessage } from "@/lib/messages"
import {
  aiSpend,
  AiSpendLine,
} from "@/features/superadmin/components/ai-spend-line"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { EmailLookup, SupportUser } from "@/types/superadmin"

export const generateMetadata = () => translatedTitle("superadmin", "zone")

const ROW = "flex items-center justify-between gap-4 p-6"

/** An account in the admin zone's support tab: its email settings (changed on its behalf, as
 * the emails tab did), the companies it's a member of and the top-ups it paid for. The API
 * answers superadmins only and logs each look. */
export default async function SupportUserPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const t = await getTranslations("superadmin")
  const roles = await getTranslations("roles")
  const locale = await getLocale()
  const [user, account, spend] = await Promise.all([
    serverFetch<SupportUser>(`/companies/superadmin/support/users/${id}`),
    serverFetch<NonNullable<EmailLookup["account"]>>(
      `/library/superadmin/emails/accounts/${id}`
    ),
    aiSpend(`user_id=${encodeURIComponent(id)}`),
  ])

  if (!user) {
    notFound()
  }

  return (
    <main className="mx-auto max-w-page space-y-10 px-6 py-12">
      <PageHeader
        back={<BackLink href="/superadmin/support">{t("support")}</BackLink>}
        title={
          <div className="space-y-1">
            <h1 className="font-heading text-3xl font-medium tracking-tight normal-case">
              {user.email ? (
                <WrappedEmail email={user.email} />
              ) : (
                t("supportNoEmail")
              )}
            </h1>
            <p className="flex flex-wrap items-center gap-x-3 text-sm text-muted-foreground">
              {user.created_at && (
                <span>
                  {t("supportCreated")} <LocalDate iso={user.created_at} />
                </span>
              )}
              <EntityId id={user.user_id} />
            </p>
          </div>
        }
      />

      <AiSpendLine spend={spend} />
      <AccountEmails account={account} />
      {account?.email && <AddressSuppression email={account.email} />}

      <section className="space-y-4">
        <h2 className="text-lg font-medium">{t("supportCompanies")}</h2>
        {user.companies.length === 0 ? (
          <p className="text-muted-foreground">{t("supportNoCompanies")}</p>
        ) : (
          <ul className={LIST_BOX}>
            {user.companies.map((company) => (
              <li key={company.id}>
                <Link
                  href={`/superadmin/support/companies/${company.id}`}
                  className={`${ROW} ${ROW_HOVER}`}
                >
                  <span className="min-w-0 text-lg font-medium break-words normal-case">
                    {company.name}
                  </span>
                  <Badge
                    variant="outline"
                    className="h-7 px-3 text-sm font-light"
                  >
                    {hasMessage(roles, company.role)
                      ? roles(company.role)
                      : company.role}
                  </Badge>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-medium">{t("supportTopUps")}</h2>
        {user.top_ups.length === 0 ? (
          <p className="text-muted-foreground">{t("supportNoTopUps")}</p>
        ) : (
          <ul className={LIST_BOX}>
            {user.top_ups.map((topUp) => (
              <li key={topUp.transaction_id} className={ROW}>
                <span className="min-w-0 space-y-1">
                  <span className="block text-lg font-medium break-words normal-case">
                    {topUp.company_name ?? t("supportDeletedCompany")}
                  </span>
                  <span className="block text-sm break-all text-muted-foreground">
                    <LocalDate iso={topUp.created_at} withTime />
                    {/* On phones the payment ID takes its own line. */}
                    <Dot className="max-sm:hidden" />
                    <span className="max-sm:block">{topUp.transaction_id}</span>
                  </span>
                </span>
                <span className="shrink-0 font-heading text-xl font-medium tabular-nums">
                  {formatPrice(Number(topUp.total), topUp.currency, locale)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  )
}
