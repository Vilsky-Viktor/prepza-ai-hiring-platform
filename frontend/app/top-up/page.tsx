import { cookies } from "next/headers"
import Link from "next/link"
import { getTranslations } from "next-intl/server"

import { BalanceRow } from "@/components/billing/balance-row"
import { CompanyCurrencySetting } from "@/components/billing/company-currency"
import { PageHeader } from "@/components/page-header"
import { RefreshOnFocus } from "@/components/billing/refresh-on-focus"
import { SignInPrompt } from "@/components/sign-in-prompt"
import { Button } from "@/components/ui/button"
import { TOKEN_COOKIE } from "@/constants/auth"
import { optionalFetch, serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import { companyCurrencyPath, visitorCatalog } from "@/lib/catalog"
import type { CompanyCurrency } from "@/types/billing"
import type { CompanyBalance } from "@/types/company"
import { LIST_BOX } from "@/constants/lists"
import { CARD } from "@/constants/cards"

export const generateMetadata = () => translatedTitle("topUp", "title")

export default async function TopUpPage() {
  const signedIn = (await cookies()).has(TOKEN_COOKIE)
  const t = await getTranslations("topUp")
  const [catalog, companies] = signedIn
    ? await Promise.all([
        visitorCatalog(),
        serverFetch<CompanyBalance[]>("/companies/companies/credits?limit=100"),
      ])
    : [null, null]
  // Each company's currency, beside its Top up.
  const currencies = await Promise.all(
    (companies ?? []).map(async (company) =>
      optionalFetch<CompanyCurrency>(await companyCurrencyPath(company.id))
    )
  )

  return (
    <main className="mx-auto max-w-page space-y-12 px-6 py-12">
      <RefreshOnFocus />
      <PageHeader
        help="topUp"
        title={
          <div className="space-y-2">
            <div className="flex items-center justify-between gap-4">
              <h1 className="font-heading text-4xl font-medium tracking-tight">
                {t("title")}
              </h1>
              <Button
                variant="outline"
                className="h-12 px-6 text-base"
                render={<Link href="/pricing" />}
                nativeButton={false}
              >
                {t("pricing")}
              </Button>
            </div>
            {catalog && (
              <p className="text-base text-muted-foreground">
                {t("intro", { credits: catalog.candidate_credits })}
              </p>
            )}
          </div>
        }
      />

      {!signedIn && <SignInPrompt />}

      {signedIn && companies && companies.length === 0 && (
        <div className={`flex flex-col items-start gap-4 ${CARD}`}>
          <p className="text-base text-muted-foreground">{t("noCompany")}</p>
          <Button
            className="h-12 px-6 text-base"
            render={<Link href="/companies" />}
            nativeButton={false}
          >
            {t("createCompany")}
          </Button>
        </div>
      )}

      {catalog && companies && companies.length > 0 && (
        <section className="space-y-4">
          {/* Each company's row lights up on hover, so the eye follows its line. */}
          <div
            className={`${LIST_BOX} overflow-hidden [&>*]:transition-colors [&>*:hover]:bg-surface`}
          >
            {companies.map((company, index) => (
              <BalanceRow
                key={company.id}
                catalog={catalog}
                name={company.name}
                available={company.available}
                low={company.low}
                companyId={company.id}
                // Only companies the user owns or administers are listed: each can change it.
                currency={
                  currencies[index] && (
                    <CompanyCurrencySetting
                      companyId={company.id}
                      canEdit
                      initial={currencies[index]}
                    />
                  )
                }
              />
            ))}
          </div>
        </section>
      )}
    </main>
  )
}
