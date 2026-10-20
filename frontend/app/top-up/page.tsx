import { cookies } from "next/headers"
import Link from "next/link"
import { getTranslations } from "next-intl/server"

import { BalanceRow } from "@/components/billing/balance-row"
import { PageHeader } from "@/components/page-header"
import { RefreshOnFocus } from "@/components/billing/refresh-on-focus"
import { SignInPrompt } from "@/components/sign-in-prompt"
import { Button } from "@/components/ui/button"
import { TOKEN_COOKIE } from "@/constants/auth"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { Catalog } from "@/types/billing"
import type { CompanyBalance } from "@/types/company"
import { LIST_BOX } from "@/constants/lists"

export const generateMetadata = () => translatedTitle("topUp", "title")

function SectionTitle({ title, note }: { title: string; note: string }) {
  return (
    <div className="space-y-1">
      <h2 className="font-heading text-2xl font-medium">{title}</h2>
      <p className="text-base text-muted-foreground">{note}</p>
    </div>
  )
}

export default async function TopUpPage() {
  const signedIn = (await cookies()).has(TOKEN_COOKIE)
  const t = await getTranslations("topUp")
  const [catalog, companies] = signedIn
    ? await Promise.all([
        serverFetch<Catalog>("/billing/catalog"),
        serverFetch<CompanyBalance[]>("/companies/companies/credits?limit=100"),
      ])
    : [null, null]

  return (
    <main className="mx-auto max-w-5xl space-y-12 px-6 py-12">
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
        <div className="flex flex-col items-start gap-4 rounded-2xl border p-6">
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
          <SectionTitle title={t("companies")} note={t("companiesNote")} />
          <div className={LIST_BOX}>
            {companies.map((company) => (
              <BalanceRow
                key={company.id}
                catalog={catalog}
                name={company.name}
                available={company.available}
                low={company.low}
                companyId={company.id}
              />
            ))}
          </div>
        </section>
      )}
    </main>
  )
}
