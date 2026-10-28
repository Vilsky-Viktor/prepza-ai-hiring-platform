import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { getTranslations } from "next-intl/server"
import { Suspense } from "react"

import { BackLink } from "@/components/common/back-link"
import {
  SlackActions,
  SlackStatus,
} from "@/components/company/slack-connection"
import { SlackKinds } from "@/components/company/slack-kinds"
import { SlackReturned } from "@/components/company/slack-returned"
import { PageHeader } from "@/components/common/page-header"
import { SignInPrompt } from "@/components/common/sign-in-prompt"
import { Dot } from "@/components/common/dot"
import { TOKEN_COOKIE } from "@/config/auth"
import { SLACK } from "@/config/slack"
import { serverFetch } from "@/lib/server-api"
import type { Company } from "@/types/company"
import type { SlackOverview } from "@/types/notifications"
import { CARD } from "@/config/cards"

export const generateMetadata = () => ({ title: SLACK.name })

/** Slack's own page, laid out like an ATS's: back to the integrations tab, its status, channel
 * and buttons; once connected, which notifications go to the channel; before, that it isn't
 * connected yet (or that Slack isn't set up on this server). */
export default async function SlackPage({
  params,
}: {
  params: Promise<{ companyId: string }>
}) {
  const { companyId } = await params
  const signedIn = (await cookies()).has(TOKEN_COOKIE)
  const t = await getTranslations("company")
  const slackText = await getTranslations("slack")
  // Asked together: the API refuses Slack's state on its own when the company isn't theirs.
  const [company, slack] = signedIn
    ? await Promise.all([
        serverFetch<Company>(`/companies/companies/${companyId}`),
        serverFetch<SlackOverview>(
          `/notifications/slack?company_id=${companyId}`
        ),
      ])
    : [null, null]

  if (!signedIn) {
    return (
      <main className="mx-auto max-w-page px-6 py-12">
        <SignInPrompt />
      </main>
    )
  }

  if (!company || !slack) {
    redirect("/companies")
  }

  return (
    <main className="mx-auto max-w-page space-y-8 px-6 py-12">
      <Suspense>
        <SlackReturned />
      </Suspense>
      <PageHeader
        back={
          <BackLink href={`/companies/${companyId}/integrations`} help="slack">
            {t("integrations")}
          </BackLink>
        }
        title={
          // On phones the buttons go on their own line, full width, sharing it equally.
          <div className="flex items-start justify-between gap-4 max-sm:flex-col max-sm:items-stretch">
            <div className="flex min-w-0 items-center gap-4">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={SLACK.logo}
                alt=""
                className="size-12 shrink-0 rounded-xl bg-surface p-2"
              />
              <div className="min-w-0 space-y-1">
                <div className="flex items-center gap-3">
                  <h1 className="font-heading text-3xl font-medium tracking-tight normal-case">
                    {SLACK.name}
                  </h1>
                  <span className="max-sm:hidden">
                    <SlackStatus slack={slack} />
                  </span>
                </div>
                {slack.connected && (
                  <p className="text-base text-muted-foreground">
                    {slack.team}
                    <Dot />
                    {slack.channel}
                  </p>
                )}
                {/* On phones "connected" goes under the name and channel. */}
                <span className="mt-2 flex empty:hidden sm:hidden">
                  <SlackStatus slack={slack} />
                </span>
              </div>
            </div>
            <div className="max-sm:mt-4 max-sm:*:w-full max-sm:*:flex-wrap max-sm:[&>*>*]:flex-1 max-sm:[&>*>*:nth-child(3)]:basis-full">
              <SlackActions
                companyId={companyId}
                slack={slack}
                canEdit={company.can_edit}
              />
            </div>
          </div>
        }
      />
      {slack.connected ? (
        <SlackKinds
          companyId={companyId}
          kinds={slack.kinds}
          allKinds={slack.all_kinds}
          canEdit={company.can_edit}
        />
      ) : (
        <p className={`${CARD} text-muted-foreground`}>
          {slackText("notConnected")}
        </p>
      )}
    </main>
  )
}
