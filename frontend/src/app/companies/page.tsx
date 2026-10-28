import { cookies } from "next/headers"
import { getTranslations } from "next-intl/server"

import { BackLink } from "@/components/common/back-link"
import { CreateCompany } from "@/features/company/components/create-company"
import { CompanyList } from "@/features/company/components/company-list"
import { PageHeader } from "@/components/common/page-header"
import { SignInPrompt } from "@/components/common/sign-in-prompt"
import { TOKEN_COOKIE } from "@/config/auth"
import { PAGE_SIZE } from "@/config/lists"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { Company } from "@/types/company"

export const generateMetadata = () => translatedTitle("company", "page")

export default async function CompanyPage() {
  const signedIn = (await cookies()).has(TOKEN_COOKIE)
  const t = await getTranslations("company")
  const common = await getTranslations("common")
  // The first page renders on the server; the rest load as the user scrolls.
  const companies = signedIn
    ? await serverFetch<Company[]>(`/companies/companies?limit=${PAGE_SIZE}`)
    : null

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <PageHeader
        back={
          <BackLink href="/" help="companies">
            {common("home")}
          </BackLink>
        }
        title={
          // On phones "new company" goes under the title, at full width.
          <div className="flex items-center justify-between gap-4 max-sm:flex-col max-sm:items-stretch">
            <h1 className="font-heading text-3xl font-medium tracking-tight">
              {t("title")}
            </h1>
            {signedIn && <CreateCompany />}
          </div>
        }
      />

      {!signedIn && <SignInPrompt />}

      {signedIn && <CompanyList initial={companies ?? []} />}
    </main>
  )
}
