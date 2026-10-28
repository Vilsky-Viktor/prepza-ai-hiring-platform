import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { BalanceRow } from "@/components/billing/balance-row"
import { CompanyCurrencySetting } from "@/components/billing/company-currency"
import { CreditHistory } from "@/components/billing/credit-history"
import { RefreshOnFocus } from "@/components/billing/refresh-on-focus"
import { ReservedList } from "@/components/billing/reserved-list"
import { CompanyHeader } from "@/components/company/company-header"
import { SignInPrompt } from "@/components/sign-in-prompt"
import { InfoCard } from "@/components/warning-card"
import { TOKEN_COOKIE } from "@/constants/auth"
import { LIST_BOX, PAGE_SIZE } from "@/constants/lists"
import { optionalFetch, serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import { companyHeaderProps } from "@/lib/company-header"
import { companyCurrencyPath, visitorCatalog } from "@/lib/catalog"
import type { Catalog, CompanyCredits, CompanyCurrency } from "@/types/billing"
import type {
  Company,
  CreditCandidate,
  CreditHistoryEntry,
} from "@/types/company"

export const generateMetadata = () => translatedTitle("company", "billing")

export default async function BillingPage({
  params,
  searchParams,
}: {
  params: Promise<{ companyId: string }>
  searchParams: Promise<{ tab?: string }>
}) {
  const { companyId } = await params
  // History opens first; the reserved candidates have their own tab, so a long list of them
  // never pushes the history out of sight.
  const tab = (await searchParams).tab === "reserved" ? "reserved" : "history"
  const t = await getTranslations("companyBilling")
  const signedIn = (await cookies()).has(TOKEN_COOKIE)
  const company = signedIn
    ? await serverFetch<Company>(`/companies/companies/${companyId}`)
    : null
  const billing = `/companies/companies/${companyId}/billing`
  const href = `/companies/${companyId}/billing`
  const [credits, catalog, currency, reserved, history] = company?.can_edit
    ? await Promise.all([
        serverFetch<CompanyCredits>(
          `/companies/companies/${companyId}/credits`
        ),
        visitorCatalog(),
        optionalFetch<CompanyCurrency>(await companyCurrencyPath(companyId)),
        // Only the open tab's first page.
        tab === "reserved"
          ? serverFetch<CreditCandidate[]>(
              `${billing}/reserved?limit=${PAGE_SIZE}`
            )
          : null,
        tab === "history"
          ? serverFetch<CreditHistoryEntry[]>(
              `${billing}/history?limit=${PAGE_SIZE}`
            )
          : null,
      ])
    : [null, null, null, null, null]

  if (!signedIn) {
    return (
      <main className="mx-auto max-w-page px-6 py-12">
        <SignInPrompt />
      </main>
    )
  }

  if (!company) {
    redirect("/companies")
  }

  // Viewers don't see the company's billing.
  if (!company.can_edit) {
    redirect(`/companies/${companyId}/interviews`)
  }

  return (
    <main className="mx-auto max-w-page space-y-12 px-6 py-12">
      <RefreshOnFocus />
      <CompanyHeader
        {...companyHeaderProps(company)}
        companyId={companyId}
        current="billing"
        // The history and the reserved candidates, each a page of billing's in the menu.
        sub={[
          { id: "history", href, label: t("history") },
          {
            id: "reserved",
            href: `${href}?tab=reserved`,
            label: t("reservedTab", {
              count: credits?.reserved_candidates ?? 0,
            }),
          },
        ]}
        currentSub={tab}
        className="space-y-12"
      >
        <Balance
          credits={credits}
          catalog={catalog}
          currency={currency}
          name={company.name}
          companyId={companyId}
          canEdit={company.can_edit}
        />
        {tab === "reserved" ? (
          <ReservedTab companyId={companyId} reserved={reserved} />
        ) : (
          <CreditHistory companyId={companyId} initial={history ?? []} />
        )}
      </CompanyHeader>
    </main>
  )
}

/** The candidates holding credits, with a note on why; a line when there are none. */
async function ReservedTab({
  companyId,
  reserved,
}: {
  companyId: string
  reserved: CreditCandidate[] | null
}) {
  const t = await getTranslations("companyBilling")

  return (
    <div className="space-y-4">
      <InfoCard className="max-sm:-mx-6 max-sm:rounded-none">
        {t("reservedNote")}
      </InfoCard>
      {reserved && reserved.length > 0 ? (
        <ReservedList companyId={companyId} initial={reserved} />
      ) : (
        <p className="py-16 text-center text-muted-foreground">
          {t("reservedEmpty")}
        </p>
      )}
    </div>
  )
}

/** The balance with its top-up, once both the credits and the prices could be read. */
function Balance({
  credits,
  catalog,
  currency,
  name,
  companyId,
  canEdit,
}: {
  credits: CompanyCredits | null
  catalog: Catalog | null
  currency: CompanyCurrency | null
  name: string
  companyId: string
  canEdit: boolean
}) {
  if (!credits || !catalog) {
    return null
  }

  return (
    <div className={LIST_BOX}>
      <BalanceRow
        catalog={catalog}
        name={name}
        available={credits.available}
        reserved={credits.reserved}
        low={credits.low}
        companyId={companyId}
        currency={
          currency && (
            <CompanyCurrencySetting
              companyId={companyId}
              canEdit={canEdit}
              initial={currency}
            />
          )
        }
      />
    </div>
  )
}
