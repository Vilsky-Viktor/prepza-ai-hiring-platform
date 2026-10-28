import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { CompanyList } from "@/components/company/company-list"
import { CreateCompany } from "@/components/company/create-company"
import { PageHeader } from "@/components/common/page-header"
import { SignInPrompt } from "@/components/common/sign-in-prompt"
import { TOKEN_COOKIE } from "@/config/auth"
import { PAGE_SIZE } from "@/config/lists"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { Company } from "@/types/company"

export const generateMetadata = () => translatedTitle("company", "pickTitle")

/** Where a free test is used for candidates (from a practice page or result): with one company,
 * straight to the test in it; otherwise the user's companies, each opening the test there, laid
 * out like the companies list. */
export default async function PickCompanyPage({
  params,
}: {
  params: Promise<{ templateId: string }>
}) {
  const { templateId } = await params
  const signedIn = (await cookies()).has(TOKEN_COOKIE)
  const t = await getTranslations("company")
  const companies = signedIn
    ? await serverFetch<Company[]>(`/companies/companies?limit=${PAGE_SIZE}`)
    : null

  if (companies?.length === 1) {
    redirect(`/companies/${companies[0].id}/templates/${templateId}`)
  }

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <PageHeader
        help="pickCompany"
        title={
          <div className="flex items-center justify-between gap-4">
            <div className="space-y-2">
              <h1 className="font-heading text-3xl font-medium tracking-tight">
                {t("pickTitle")}
              </h1>
              <p className="text-base text-muted-foreground">{t("pickText")}</p>
            </div>
            {signedIn && <CreateCompany templateId={templateId} />}
          </div>
        }
      />

      {!signedIn && <SignInPrompt />}

      {signedIn && (
        <CompanyList initial={companies ?? []} templateId={templateId} />
      )}
    </main>
  )
}
