"use client"

import Link from "next/link"
import { useTranslations } from "next-intl"
import { useEffect } from "react"

import { useAuth } from "@/providers/auth-provider"
import { BackLink } from "@/components/back-link"
import { CompanyLogo } from "@/components/company/company-logo"
import { SessionPlay } from "@/components/company/session-play"
import { SignInPrompt } from "@/components/sign-in-prompt"
import { Button } from "@/components/ui/button"
import { useSessionPlayer } from "@/hooks/use-session-player"
import { useSessionBrand } from "@/hooks/use-session-brand"
import { useSessionDone } from "@/hooks/use-session-done"
import { bdi } from "@/lib/bidi"
import { setTimedPageOver } from "@/lib/timed-page"
import type { Brand } from "@/types/company"

/** The test a candidate takes; for a company member's preview, `testHref` is the test's page:
 * while playing, the back arrow goes to its interview list, and once finished, a button does. */
export function SessionView({
  id,
  testHref,
  onFinished,
}: {
  id: string
  testHref?: string
  // Embedded in a company's site: told once it's finished, which takes the candidate on.
  onFinished?: (candidateId: string) => void
}) {
  const interviews = useTranslations("interviews")
  const back = testHref && (
    <BackLink
      href={testHref.slice(0, testHref.lastIndexOf("/"))}
      className="max-sm:mb-0"
    >
      {interviews("title")}
    </BackLink>
  )
  const { user, loading } = useAuth()
  const {
    session,
    question,
    topics,
    done,
    missing,
    failed,
    retry,
    finishing,
    answer,
    advance,
    finishInterview,
  } = useSessionPlayer(id)
  const inviteId = session?.candidate_invite_id
  const practice = Boolean(session?.practice)
  useSessionDone(done, inviteId, practice, onFinished)
  const brand = useSessionBrand(testHref, inviteId, practice)
  const signedOut = !loading && !user

  // The header and footer come back if no question was ever on the clock: signed out, not found,
  // failed. A company's interview stays without them once finished, showing the company only;
  // a practice round goes on to its results, which have them.
  const over = signedOut || missing || failed

  useEffect(() => {
    setTimedPageOver(over)

    return () => setTimedPageOver(false)
  }, [over])

  if (signedOut) {
    return <SignInPrompt />
  }

  if (missing || failed) {
    return <SessionProblem missing={missing} onRetry={retry} />
  }

  if (!session) {
    return null
  }

  const progress = topics.reduce(
    (sum, topic) => ({
      answered: sum.answered + topic.answered,
      total: sum.total + topic.total,
    }),
    { answered: 0, total: 0 }
  )

  if (!question) {
    // A practice round goes on to its results instead.
    if (!done || session.practice) {
      return null
    }

    return (
      <SessionFinished
        brand={brand}
        title={session.interview_title ?? session.topic_title}
        embedded={Boolean(onFinished)}
        testHref={testHref}
      />
    )
  }

  const section = {
    number: topics.findIndex((topic) => topic.id === session.id) + 1,
    count: topics.length,
  }

  return (
    <SessionPlay
      session={session}
      progress={progress}
      section={section}
      question={question}
      onAnswer={answer}
      onAdvance={advance}
      onFinish={finishInterview}
      finishing={finishing}
      back={back}
      brand={
        <SessionLogo
          brand={brand}
          className="h-14 w-auto max-w-32 shrink-0 rounded-xl object-contain"
        />
      }
    />
  )
}

/** A company's interview once finished: the company's logo over the title, as on the
 * invitation, between the header and footer, which are back. Sent from the company's own
 * platform, a button back there; a member's preview, a button to the test. */
function SessionFinished({
  brand,
  title,
  embedded,
  testHref,
}: {
  brand: Brand | null
  title: string
  embedded: boolean
  testHref?: string
}) {
  const t = useTranslations("session")

  return (
    <div className="flex flex-col items-center gap-8 py-24 text-center">
      <SessionLogo
        brand={brand}
        className="h-20 w-auto max-w-40 rounded-xl object-contain"
      />
      <div className="space-y-3">
        <h1 className="font-heading text-3xl font-medium tracking-tight text-balance normal-case">
          {title}
        </h1>
        <p className="text-muted-foreground">{t("done")}</p>
      </div>
      {embedded ? null : brand?.return_url ? (
        <Button
          className="h-12 px-6 text-base"
          render={<a href={brand.return_url} />}
          nativeButton={false}
        >
          {t.rich("backTo", { company: brand.company, ...bdi })}
        </Button>
      ) : (
        testHref && (
          <Button
            className="h-12 px-6 text-base"
            render={
              <Link href={testHref.slice(0, testHref.lastIndexOf("/"))} />
            }
            nativeButton={false}
          >
            {t("toTest")}
          </Button>
        )
      )}
    </div>
  )
}

/** The company's logo, when it has one. */
function SessionLogo({
  brand,
  className,
}: {
  brand: Brand | null
  className: string
}) {
  if (!brand?.logo_url) {
    return null
  }

  return (
    <CompanyLogo
      url={brand.logo_url}
      name={brand.company}
      className={className}
    />
  )
}

/** A test that isn't there, or couldn't start (with a retry). */
function SessionProblem({
  missing,
  onRetry,
}: {
  missing: boolean
  onRetry: () => void
}) {
  const t = useTranslations("session")
  const common = useTranslations("common")

  if (missing) {
    return (
      <p className="py-24 text-center text-base text-muted-foreground">
        {t("missing")}
      </p>
    )
  }

  return (
    <div className="flex flex-col items-center gap-6 py-24 text-center">
      <p className="text-base text-muted-foreground">{t("startFailed")}</p>
      <Button className="h-12 px-6 text-base" onClick={onRetry}>
        {common("retry")}
      </Button>
    </div>
  )
}
