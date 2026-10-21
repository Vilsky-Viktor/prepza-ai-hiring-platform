"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { useSignIn } from "@/components/sign-in-dialog"
import { useAuth } from "@/components/auth-provider"
import { InviteIntro } from "@/components/company/invite-intro"
import { LinkStatus } from "@/components/link-status"
import { apiErrorMessage, apiFetch, serviceRefusal } from "@/lib/api"
import { humanHeaders } from "@/lib/human-check"
import { refreshVerification } from "@/lib/auth"
import { useBrandColors } from "@/hooks/use-brand-colors"
import { useLinkData } from "@/hooks/use-link-data"
import type { JobLink, SessionSummary } from "@/types/company"
import { StartPledge } from "@/features/company/components/start-pledge"

/** What someone sees from a test's shareable link: the same intro as an invite; starting signs
 * them in with Google first, which gives their name and verified email. */
export function LinkView({ token }: { token: string }) {
  const t = useTranslations("invite")
  const share = useTranslations("share")
  const session = useTranslations("session")
  const signIn = useSignIn()
  const router = useRouter()
  const { user, loading } = useAuth()
  const [starting, setStarting] = useState(false)

  // Once sign-in is known, and again after signing in, so a finished test is never offered.
  const {
    data: link,
    status,
    retry,
    gone,
  } = useLinkData<JobLink>(
    loading ? null : `/companies/links/${token}`,
    user?.uid
  )
  useBrandColors(link?.brand_colors, null, link?.brand_style)

  async function start(pledged: boolean) {
    setStarting(true)

    if (!user && !(await signIn())) {
      setStarting(false)

      return
    }

    await refreshVerification()

    try {
      const result = await apiFetch<{ sessions: SessionSummary[] }>(
        `/companies/links/${token}/start`,
        // A new candidate shows they're a person.
        {
          method: "POST",
          headers: await humanHeaders(),
          body: JSON.stringify({ pledged }),
        }
      )
      const next =
        result.sessions.find((item) => item.status !== "finished") ??
        result.sessions[0]

      if (next) {
        router.push(`/sessions/${next.id}`)

        return
      }
    } catch (error) {
      // Already finished, the company has stopped taking candidates, or their email isn't
      // confirmed yet: the API says which.
      toast.error(
        serviceRefusal(error, [403, 409]) ??
          apiErrorMessage(error, session("startFailed"))
      )
    }

    setStarting(false)
  }

  if (status !== "ready" || !link) {
    return (
      <LinkStatus
        status={status === "ready" ? "loading" : status}
        invalid={gone ?? share("invalid")}
        onRetry={retry}
      />
    )
  }

  return (
    <InviteIntro
      company={link.company}
      logoUrl={link.logo_url}
      verifiedDomain={link.verified_domain}
      title={link.title}
      questionSeconds={link.question_seconds}
      totalMinutes={link.total_minutes}
      finished={link.status === "finished"}
      viaLink
      action={
        <StartPledge
          label={link.status === "in_process" ? t("continue") : t("start")}
          pledge={link.status !== "in_process"}
          busy={starting}
          onStart={start}
        />
      }
    />
  )
}
