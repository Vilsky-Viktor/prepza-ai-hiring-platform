import { redirect } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { BackLink } from "@/components/back-link"
import { NewInterview } from "@/components/company/new-interview"
import { PausedNotice } from "@/components/paused-notice"
import { SignInPage } from "@/components/sign-in-page"
import { isPaused } from "@/lib/pause"
import { serverFetch, signedIn } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { Company } from "@/types/company"

export const generateMetadata = () => translatedTitle("interviews", "new")

export default async function NewInterviewPage({
  params,
}: {
  params: Promise<{ companyId: string }>
}) {
  if (!(await signedIn())) {
    return <SignInPage />
  }

  const { companyId } = await params
  const t = await getTranslations("interviews")
  // Asked together: the pause is the platform's, not the company's.
  const [company, paused] = await Promise.all([
    serverFetch<Company>(`/companies/companies/${companyId}`),
    isPaused(),
  ])

  // Viewers don't create tests: back to the company's tests.
  if (company && !company.can_edit) {
    redirect(`/companies/${companyId}/interviews`)
  }

  // Laid out like the home page's start: a title and the box, nothing else.
  return (
    <main className="mx-auto max-w-5xl px-6">
      <div className="flex min-h-[calc(100svh-3.5rem)] flex-col items-center justify-center pb-24">
        <div className="w-full max-w-176 space-y-10">
          <div className="relative">
            <BackLink
              href={`/companies/${companyId}/interviews`}
              help="newInterview"
              className="xl:top-2.5"
            >
              {t("title")}
            </BackLink>
            <h1 className="font-heading text-5xl font-medium tracking-tight text-balance sm:text-6xl">
              {t("createTitle")}
            </h1>
          </div>
          <PausedNotice paused={paused} />
          {/* While paused, nothing can be generated: the box is there but off. */}
          <NewInterview companyId={companyId} disabled={paused} />
        </div>
      </div>
    </main>
  )
}
