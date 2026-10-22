import { cookies } from "next/headers"
import Link from "next/link"
import { notFound } from "next/navigation"
import { getLocale, getTranslations } from "next-intl/server"

import { GradeBlock, GradeCard } from "@/components/grade-card"
import { BackLink } from "@/components/back-link"
import { PageHeader } from "@/components/page-header"
import { HireWithTemplate } from "@/components/practice/hire-with-template"
import { PracticeActions } from "@/components/practice/practice-actions"
import { PracticeReview } from "@/components/practice/practice-review"
import { SignInPrompt } from "@/components/sign-in-prompt"
import { Button } from "@/components/ui/button"
import { TOKEN_COOKIE } from "@/constants/auth"
import { publicFetch, serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { PracticeRound, PracticeSize } from "@/types/round"
import { formatPercent } from "@/lib/format"
import { PageKey } from "@/components/page-key"

export const generateMetadata = () => translatedTitle("practice", "results")

/** A talent's practice round: the grade, each topic's score, and every question with the
 * right answer and their own pick. An unfinished round offers to continue it. */
export default async function PracticeRoundPage({
  params,
}: {
  params: Promise<{ roundId: string }>
}) {
  const { roundId } = await params
  const t = await getTranslations("practice")
  const locale = await getLocale()

  if (!(await cookies()).has(TOKEN_COOKIE)) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-12">
        <PageKey page="practiceRound" />
        <SignInPrompt />
      </main>
    )
  }

  const round = await serverFetch<PracticeRound>(
    `/rounds/practice/rounds/${roundId}`
  )

  if (!round) {
    notFound()
  }

  // The times per question to choose from for another round.
  const size = round.finished
    ? await publicFetch<PracticeSize>(
        `/rounds/practice/${round.template_id}/size`
      )
    : null

  return (
    <main className="mx-auto max-w-5xl space-y-10 px-6 py-12">
      <PageKey page="practiceRound" />
      <PageHeader
        back={
          <BackLink href={`/practice/${round.template_id}`}>
            {t("title")}
          </BackLink>
        }
        title={
          // On phones the actions take their own line under the title, centered.
          <div className="flex items-start justify-between gap-4 max-sm:flex-wrap">
            <h1 className="min-w-0 flex-1 font-heading text-3xl font-medium tracking-tight text-balance normal-case">
              {round.title ?? t("title")}
            </h1>
            {round.finished && (
              <div className="max-sm:flex max-sm:basis-full max-sm:justify-center max-sm:py-4">
                <PracticeActions
                  templateId={round.template_id}
                  startLabel={t("again")}
                  timings={size?.timings ?? []}
                />
              </div>
            )}
          </div>
        }
      />

      {!round.finished && round.open_session_id ? (
        <div className="space-y-6 py-12 text-center">
          <p className="text-base text-muted-foreground">{t("notFinished")}</p>
          <Button
            className="h-12 px-6 text-base"
            render={<Link href={`/sessions/${round.open_session_id}`} />}
            nativeButton={false}
          >
            {t("continue")}
          </Button>
        </div>
      ) : (
        <>
          {/* The grade, and how many the talent picked an answer for. */}
          <GradeCard>
            <GradeBlock
              value={formatPercent(round.grade ?? 0, locale)}
              label={t("grade")}
            />
            <GradeBlock
              value={
                <>
                  {round.answered}
                  {/* The total smaller, so the answered count stands out. */}
                  <span className="text-3xl">/{round.total}</span>
                </>
              }
              label={t("answeredLabel")}
            />
          </GradeCard>
          {round.topics.map((topic) => (
            <section key={topic.title} className="space-y-4">
              {/* On phones the topic, then its grade under it, centered. */}
              <div className="flex items-center justify-between gap-4 max-sm:flex-col max-sm:text-center">
                <h2 className="font-heading text-2xl font-medium normal-case">
                  {topic.title}
                </h2>
                <p className="w-24 text-center">
                  <span className="block text-4xl font-light tabular-nums">
                    {formatPercent(topic.score, locale)}
                  </span>
                  <span className="block text-sm text-muted-foreground">
                    {t("gradeLabel")}
                  </span>
                </p>
              </div>
              <PracticeReview
                sessionId={topic.session_id}
                items={topic.review}
                language={round.language}
              />
            </section>
          ))}
        </>
      )}

      {/* Having just taken it, a hiring manager knows what their candidates would get. */}
      <HireWithTemplate templateId={round.template_id} />
    </main>
  )
}
