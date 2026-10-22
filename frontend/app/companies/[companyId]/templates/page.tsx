import { ArrowRightIcon, InfoIcon } from "lucide-react"
import Link from "next/link"
import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { CompanyHeader } from "@/components/company/company-header"
import { SignInPrompt } from "@/components/sign-in-prompt"
import { Button } from "@/components/ui/button"
import {
  TemplateBrowser,
  type TemplateSearchParams,
} from "@/components/templates/template-browser"
import { TOKEN_COOKIE } from "@/constants/auth"
import { serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import { companyHeaderProps } from "@/lib/company-header"
import type { Company } from "@/types/company"

export const generateMetadata = () => translatedTitle("templates", "title")

/** Templates a company starts a test from, searched like the superadmin's list; using one copies
 * it into the company's own test. */
export default async function CompanyTemplatesPage({
  params,
  searchParams,
}: {
  params: Promise<{ companyId: string }>
  searchParams: Promise<TemplateSearchParams>
}) {
  const { companyId } = await params
  const t = await getTranslations("templates")
  const interviewsText = await getTranslations("interviews")
  const signedIn = (await cookies()).has(TOKEN_COOKIE)
  const company = signedIn
    ? await serverFetch<Company>(`/companies/companies/${companyId}`)
    : null

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

  const browser = await TemplateBrowser({
    base: `/companies/${companyId}/templates`,
    // Only templates a company can copy, so "use template" never fails.
    listPath: "/library/templates/copyable",
    params: await searchParams,
    openBase: `/companies/${companyId}/templates`,
    // Using a template creates a test: not for viewers.
    companyId: company.can_edit ? companyId : undefined,
  })

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <CompanyHeader
        {...companyHeaderProps(company)}
        companyId={companyId}
        current="templates"
      >
        {/* Templates are generic; an interview from the job description fits the role closer. */}
        <div className="flex items-center gap-4 rounded-2xl bg-muted p-5 text-base">
          <div className="flex flex-1 items-center gap-4">
            <InfoIcon aria-hidden className="size-6 shrink-0 text-primary" />
            <p className="text-muted-foreground">
              {t.rich("warningText", {
                b: (chunks) => (
                  <span className="font-medium text-foreground">{chunks}</span>
                ),
              })}
            </p>
          </div>
          {company.can_edit && (
            <Button
              size="icon"
              aria-label={interviewsText("new")}
              render={<Link href={`/companies/${companyId}/interviews/new`} />}
              nativeButton={false}
              className="size-10 shrink-0"
            >
              <ArrowRightIcon aria-hidden className="size-5 rtl:-scale-x-100" />
            </Button>
          )}
        </div>
        {browser}
      </CompanyHeader>
    </main>
  )
}
