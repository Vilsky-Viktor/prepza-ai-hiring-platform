"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useEffect, useState } from "react"
import { toast } from "sonner"

import { useAuth } from "@/providers/auth-provider"
import { BackLink } from "@/components/back-link"
import { CancelGeneration } from "@/components/generation/cancel-generation"
import { GenerationProgress } from "@/components/generation/generation-progress"
import { TopicReview } from "@/components/generation/topic-review"
import { SignInPrompt } from "@/components/sign-in-prompt"
import { Button } from "@/components/ui/button"
import { useGenerationPoll } from "@/hooks/use-generation-poll"
import { useHumanCheck } from "@/hooks/use-human-check"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { humanHeaders } from "@/lib/human-check"
import { topUpAction } from "@/lib/credits"
import type { DraftTopic, Generation } from "@/types/generation"

export function GenerationView({
  path,
  next,
  backHref,
  backLabel,
}: {
  path: string
  // Where to go once the test is ready.
  next: string
  backHref: string
  backLabel: string
}) {
  const t = useTranslations("generation")
  useHumanCheck()
  const billing = useTranslations("billing")
  const { user, loading } = useAuth()
  const router = useRouter()
  const [generation, setGeneration] = useState<Generation | null>(null)
  const [missing, setMissing] = useState(false)
  // Bumped after a review so polling starts again.
  const [round, setRound] = useState(0)

  useGenerationPoll<Generation>(user ? path : null, round, setGeneration, () =>
    setMissing(true)
  )

  useEffect(() => {
    if (generation?.status === "done") {
      router.replace(next)
    }
  }, [generation, next, router])

  async function submitReview(
    selected: number[],
    instructions: string,
    topics: DraftTopic[] | null
  ) {
    try {
      // A company that never paid shows it's a person before its questions are made.
      const next = await apiFetch<Generation>(`${path}/review`, {
        method: "POST",
        body: JSON.stringify({ selected, instructions, topics }),
        headers: await humanHeaders(),
      })
      setGeneration(next)
      setRound((value) => value + 1)
    } catch (error) {
      // Without enough credits the draft waits; the toast offers the top-up page.
      toast.error(
        apiErrorMessage(error, t("reviewFailed")),
        topUpAction(error, billing("topUp"), () => router.push("/top-up"))
      )
    }
  }

  async function retry() {
    try {
      const next = await apiFetch<Generation>(`${path}/retry`, {
        method: "POST",
      })
      setGeneration(next)
      setRound((value) => value + 1)
    } catch (error) {
      toast.error(
        apiErrorMessage(error, t("retryFailed")),
        topUpAction(error, billing("topUp"), () => router.push("/top-up"))
      )
    }
  }

  if (!loading && !user) {
    return (
      <WithBack href={backHref} label={backLabel}>
        <SignInPrompt />
      </WithBack>
    )
  }

  if (missing) {
    return (
      <WithBack href={backHref} label={backLabel}>
        <Message back={backHref} text={t("missing")} />
      </WithBack>
    )
  }

  if (generation?.status === "cancelled") {
    return (
      <WithBack href={backHref} label={backLabel}>
        <Message back={backHref} text={t("cancelled")} />
      </WithBack>
    )
  }

  const cancel = <CancelGeneration path={path} leaveTo={backHref} />

  if (generation?.status === "failed") {
    return (
      <WithBack href={backHref} label={backLabel}>
        <Message back={backHref} text={t("failed")} onRetry={retry} />
        {cancel && <div className="flex justify-center">{cancel}</div>}
      </WithBack>
    )
  }

  if (generation?.status === "awaiting_review" && generation.topics) {
    return (
      <TopicReview
        key={round}
        topics={generation.topics}
        maxTopics={generation.max_topics}
        maxSubtopics={generation.max_subtopics}
        back={
          <BackLink href={backHref} help="reviewTopics">
            {backLabel}
          </BackLink>
        }
        cancel={cancel}
        onSubmit={submitReview}
      />
    )
  }

  if (!generation || generation.status === "done") {
    return null
  }

  return (
    <GenerationProgress
      generation={generation}
      backHref={backHref}
      backLabel={backLabel}
      action={cancel}
    />
  )
}

function WithBack({
  href,
  label,
  children,
}: {
  href: string
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="relative">
      <BackLink href={href}>{label}</BackLink>
      {children}
    </div>
  )
}

function Message({
  back,
  text,
  onRetry,
}: {
  // The company's tests, where a new one can be started.
  back: string
  text: string
  onRetry?: () => Promise<void>
}) {
  const t = useTranslations("generation")
  const [retrying, setRetrying] = useState(false)

  async function retry() {
    setRetrying(true)
    await onRetry?.()
    setRetrying(false)
  }

  return (
    <div className="flex flex-col items-center gap-8 py-24 text-center">
      <p className="text-base text-muted-foreground">{text}</p>
      <div className="flex flex-wrap justify-center gap-3">
        {onRetry && (
          <Button
            className="h-12 px-6 text-base"
            disabled={retrying}
            onClick={retry}
          >
            {retrying ? t("retrying") : t("retry")}
          </Button>
        )}
        <Button
          variant="outline"
          className="h-12 px-6 text-base"
          render={<Link href={back} />}
          nativeButton={false}
        >
          {t("startOver")}
        </Button>
      </div>
    </div>
  )
}
