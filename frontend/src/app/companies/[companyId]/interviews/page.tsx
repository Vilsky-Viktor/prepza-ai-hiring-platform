import { cookies } from "next/headers"
import Link from "next/link"
import { getTranslations } from "next-intl/server"
import { redirect } from "next/navigation"

import { CompanyCredits as CreditsPanel } from "@/components/company/company-credits"
import { CompanyHeader } from "@/components/company/company-header"
import { InterviewList } from "@/components/company/interview-list"
import { InterviewSearch } from "@/components/company/interview-search"
import { SearchedList } from "@/components/common/searched-list"
import { SignInPrompt } from "@/components/common/sign-in-prompt"
import { Button } from "@/components/ui/button"
import { TOKEN_COOKIE } from "@/config/auth"
import { PAGE_SIZE } from "@/config/lists"
import { optionalFetch, serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import { companyHeaderProps } from "@/lib/company-header"
import type { CompanyCredits } from "@/types/billing"
import type { Company, Interview } from "@/types/company"

export const generateMetadata = () => translatedTitle("interviews", "title")

/** A company's interviews, searched by title (`?q=`, kept in the address like the templates'). */
export default async function InterviewsPage({
  params,
  searchParams,
}: {
  params: Promise<{ companyId: string }>
  searchParams: Promise<{ q?: string }>
}) {
  const { companyId } = await params
  const q = (await searchParams).q?.trim() ?? ""
  const listPath = `/companies/interviews?company_id=${companyId}${q ? `&q=${encodeURIComponent(q)}` : ""}`
  const t = await getTranslations("interviews")
  const signedIn = (await cookies()).has(TOKEN_COOKIE)
  // Asked together: the API refuses each on its own when the company isn't theirs.
  const [company, interviews, credits] = signedIn
    ? await Promise.all([
        serverFetch<Company>(`/companies/companies/${companyId}`),
        serverFetch<Interview[]>(`${listPath}&limit=${PAGE_SIZE}`),
        optionalFetch<CompanyCredits>(
          `/companies/companies/${companyId}/credits`
        ),
      ])
    : [null, null, null]

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

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <CompanyHeader
        {...companyHeaderProps(company)}
        companyId={companyId}
        current="interviews"
        action={
          <div className="flex shrink-0 items-center gap-6 max-sm:flex-col max-sm:items-stretch max-sm:gap-3">
            {credits != null && (
              <CreditsPanel
                companyId={companyId}
                companyName={company.name}
                credits={credits.available}
                low={credits.low}
                canEdit={company.can_edit}
              />
            )}
            {company.can_edit && (
              <Button
                render={
                  <Link href={`/companies/${companyId}/interviews/new`} />
                }
                nativeButton={false}
                className="h-12 px-6 text-base"
              >
                {t("new")}
              </Button>
            )}
          </div>
        }
      >
        <SearchedList>
          <InterviewSearch
            action={`/companies/${companyId}/interviews`}
            q={q}
          />
          {interviews && (
            <InterviewList
              companyId={companyId}
              path={listPath}
              initial={interviews}
              canEdit={company.can_edit}
              searched={Boolean(q)}
            />
          )}
        </SearchedList>
      </CompanyHeader>
    </main>
  )
}
