import { notFound } from "next/navigation"
import { getTranslations } from "next-intl/server"

import { BackLink } from "@/components/common/back-link"
import { BrandColorsOn } from "@/features/company/components/brand-colors-on"
import { InviteIntro } from "@/components/common/invite-intro"
import { StartPreview } from "@/features/company/components/start-preview"
import { SignInPage } from "@/components/common/sign-in-page"
import { serverFetch, signedIn } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { Company, InterviewDetail } from "@/types/company"
import { START_PAGE } from "@/config/start-page"

export const generateMetadata = () => translatedTitle("invite", "title")

/** A company member tries their test: the same intro a candidate gets, then the test, free. */
export default async function TryInterviewPage({
  params,
}: {
  params: Promise<{ companyId: string; id: string }>
}) {
  if (!(await signedIn())) {
    return <SignInPage />
  }

  const { companyId, id } = await params
  const interviews = await getTranslations("interviews")
  const [company, interview] = await Promise.all([
    serverFetch<Company>(`/companies/companies/${companyId}`),
    serverFetch<InterviewDetail>(`/companies/interviews/${id}`),
  ])

  if (!company || !interview?.set_id) {
    notFound()
  }

  // Laid out like the candidate's invite page.
  return (
    <main className={START_PAGE}>
      <BrandColorsOn
        colors={company.candidate_colors ?? null}
        look={company.brand_style ?? null}
      />
      {/* Only a member's preview has a way back, beside the intro as on other pages; narrower,
          at the top of the test's column. */}
      <div className="relative w-full">
        <InviteIntro
          company={company.name}
          logoUrl={company.logo_url}
          verifiedDomain={company.verified_domain}
          title={interview.title}
          questionSeconds={interview.question_seconds}
          totalMinutes={interview.total_minutes}
          voice={interview.voice}
          finished={false}
          back={
            <BackLink
              href={`/companies/${companyId}/interviews`}
              help="tryInterview"
            >
              {interviews("title")}
            </BackLink>
          }
          action={
            <StartPreview
              companyId={companyId}
              interviewId={id}
              voice={interview.voice}
            />
          }
        />
      </div>
    </main>
  )
}
