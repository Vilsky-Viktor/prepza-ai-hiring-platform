import { cookies } from "next/headers"
import { getTranslations } from "next-intl/server"

import { BackLink } from "@/components/back-link"
import { PageHeader } from "@/components/page-header"
import { PracticeRoundList } from "@/components/practice/practice-round-list"
import { StartPractice } from "@/components/practice/start-practice"
import { SignInPrompt } from "@/components/sign-in-prompt"
import { TOKEN_COOKIE } from "@/constants/auth"
import { publicFetch, serverFetch } from "@/lib/server-api"
import { translatedTitle } from "@/lib/site"
import type { PracticeRoundSummary, PracticeSize } from "@/types/round"
import type { Template } from "@/types/superadmin"
import { PAGE_SIZE } from "@/constants/lists"
import { PageKey } from "@/components/page-key"

export const generateMetadata = () => translatedTitle("practice", "history")

/** A talent's rounds on one practice test, newest first, a page at a time, with their grades,
 * to see progress. Each opens its results. */
export default async function PracticeHistoryPage({
  params,
}: {
  params: Promise<{ templateId: string }>
}) {
  const { templateId } = await params
  const t = await getTranslations("practice")

  if (!(await cookies()).has(TOKEN_COOKIE)) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-12">
        <PageKey page="practiceHistory" />
        <SignInPrompt />
      </main>
    )
  }

  const [template, rounds, size] = await Promise.all([
    serverFetch<Template>(`/library/templates/${templateId}`),
    serverFetch<PracticeRoundSummary[]>(
      `/rounds/practice/${templateId}/rounds?limit=${PAGE_SIZE}`
    ),
    publicFetch<PracticeSize>(`/rounds/practice/${templateId}/size`),
  ])

  return (
    <main className="mx-auto max-w-5xl space-y-8 px-6 py-12">
      <PageKey page="practiceHistory" />
      <PageHeader
        back={
          <BackLink href={`/practice/${templateId}`}>{t("title")}</BackLink>
        }
        title={
          // On phones "practice again" takes its own line, at full width.
          <div className="flex items-start justify-between gap-4 max-sm:flex-col max-sm:items-stretch">
            <div className="min-w-0 flex-1 space-y-1">
              <h1 className="font-heading text-3xl font-medium tracking-tight">
                {t("history")}
              </h1>
              {template && (
                <p className="text-base text-muted-foreground normal-case">
                  {template.title}
                </p>
              )}
            </div>
            <div className="max-sm:py-4 max-sm:*:w-full">
              <StartPractice
                templateId={templateId}
                label={t("again")}
                timings={size?.timings ?? []}
              />
            </div>
          </div>
        }
      />

      <PracticeRoundList templateId={templateId} initial={rounds ?? []} />
    </main>
  )
}
