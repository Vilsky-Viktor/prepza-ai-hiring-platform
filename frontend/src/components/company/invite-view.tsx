"use client"

import { useRouter, useSearchParams } from "next/navigation"
import { useTranslations } from "next-intl"
import { useEffect, useState } from "react"
import { toast } from "sonner"

import { useAuth } from "@/components/auth-provider"
import { InviteIntro } from "@/components/company/invite-intro"
import { LinkStatus } from "@/components/link-status"
import { useSignIn } from "@/components/sign-in-dialog"
import { Button } from "@/components/ui/button"
import { WarningCard } from "@/components/warning-card"
import { apiErrorMessage, apiFetch, serviceRefusal } from "@/lib/api"
import { refreshVerification, signInAsGuest } from "@/lib/auth"
import { useBrandColors } from "@/hooks/use-brand-colors"
import { useLinkData } from "@/hooks/use-link-data"
import type { InviteView as Invite, SessionSummary } from "@/types/company"
import { START_BUTTON } from "@/config/start-page"
import { StartPledge } from "@/features/company/components/start-pledge"

/** The invitation. Embedded in a company's site, `onStarted` opens the interview in place
 * instead of going to its page, and `onUnavailable` hears when the link can't be read. */
export function InviteView({
  token,
  onStarted,
  onUnavailable,
}: {
  token: string
  onStarted?: (sessionId: string) => void
  onUnavailable?: (status: "missing" | "failed") => void
}) {
  const share = useTranslations("share")
  const session = useTranslations("session")
  const router = useRouter()
  const { user, loading } = useAuth()
  const signIn = useSignIn()
  const [starting, setStarting] = useState(false)
  // Read signed in or not, so a visitor sees what the invitation is for before signing in;
  // again after signing in, for whose it is.
  const {
    data: invite,
    status,
    retry,
    gone,
  } = useLinkData<Invite>(
    loading ? null : `/companies/invites/${token}`,
    user?.uid
  )

  useBrandColors(invite?.brand_colors, invite?.theme, invite?.brand_style)

  useEffect(() => {
    if (status === "missing" || status === "failed") {
      onUnavailable?.(status)
    }
  }, [status, onUnavailable])
  // A theme the address asks for goes on with the candidate to the questions.
  const asked = useSearchParams().get("theme")

  async function start(pledged: boolean) {
    setStarting(true)

    try {
      // Sent by the company's own platform: the link signs the candidate in.
      if (invite?.guest) {
        const guest = await apiFetch<{ token: string }>(
          `/companies/invites/${token}/guest`,
          { method: "POST" }
        )
        await signInAsGuest(guest.token)
      } else {
        await refreshVerification()
      }

      const result = await apiFetch<{ sessions: SessionSummary[] }>(
        `/companies/invites/${token}/start`,
        { method: "POST", body: JSON.stringify({ pledged }) }
      )

      const next =
        result.sessions.find((item) => item.status !== "finished") ??
        result.sessions[0]

      if (next && onStarted) {
        onStarted(next.id)

        return
      }

      if (next) {
        router.push(
          `/sessions/${next.id}${asked ? `?theme=${encodeURIComponent(asked)}` : ""}`
        )

        return
      }

      setStarting(false)
    } catch (error) {
      // Another email, or theirs not confirmed yet, or the pause: the API says which.
      toast.error(
        serviceRefusal(error, [403, 409]) ??
          apiErrorMessage(error, session("startFailed"))
      )
      setStarting(false)
    }
  }

  if (status !== "ready" || !invite) {
    return (
      <LinkStatus
        status={status === "ready" ? "loading" : status}
        invalid={gone ?? share("invalid")}
        onRetry={retry}
      />
    )
  }

  // The backend says whether the invite is this account's.
  const matches = invite.matches ?? false

  return (
    <InviteIntro
      company={invite.company}
      logoUrl={invite.logo_url}
      verifiedDomain={invite.verified_domain}
      title={invite.title}
      questionSeconds={invite.question_seconds}
      totalMinutes={invite.total_minutes}
      finished={invite.status === "finished"}
      fillScreen={!onStarted}
      action={
        <InviteAction
          guest={invite.guest}
          signedIn={!!user}
          matches={matches}
          inProcess={invite.status === "in_process"}
          starting={starting}
          onSignIn={() => signIn()}
          onStart={start}
        />
      }
    />
  )
}

/** A guest's link is all they need; anyone else signs in with the invited email. Signed in
 * with another email: a warning, in the warning card. */
function InviteAction({
  guest,
  signedIn,
  matches,
  inProcess,
  starting,
  onSignIn,
  onStart,
}: {
  guest: boolean | undefined
  signedIn: boolean
  matches: boolean
  inProcess: boolean
  starting: boolean
  onSignIn: () => void
  onStart: (pledged: boolean) => void
}) {
  const t = useTranslations("invite")

  if (!guest && !signedIn) {
    return (
      <Button className={START_BUTTON} onClick={onSignIn}>
        {t("signInToStart")}
      </Button>
    )
  }

  if (guest || matches) {
    return (
      <StartPledge
        label={inProcess ? t("continue") : t("start")}
        pledge={!inProcess}
        busy={starting}
        onStart={onStart}
      />
    )
  }

  return <WarningCard className="text-start">{t("mismatch")}</WarningCard>
}
