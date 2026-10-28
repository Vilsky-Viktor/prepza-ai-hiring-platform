"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { COMPANIES_CHANGED } from "@/config/notifications"
import { useAuth } from "@/providers/auth-provider"
import { useSignIn } from "@/components/common/sign-in-dialog"
import { LinkStatus } from "@/components/common/link-status"
import { Button } from "@/components/ui/button"
import { InfoCard, WarningCard } from "@/components/common/warning-card"
import { ApiError, apiFetch } from "@/lib/api"
import { useLinkData } from "@/hooks/use-link-data"
import type { AdminInvite as Invite } from "@/types/company"

export function AdminInvite({ token }: { token: string }) {
  const t = useTranslations("company")
  const share = useTranslations("share")
  const router = useRouter()
  const { user, loading } = useAuth()
  const signIn = useSignIn()
  const [accepting, setAccepting] = useState(false)
  // Read signed in or not, so a visitor sees what the invitation is for before signing in;
  // again after signing in, for whose it is.
  const {
    data: invite,
    status,
    retry,
  } = useLinkData<Invite>(
    loading ? null : `/companies/members/invites/${token}`,
    user?.uid
  )

  async function accept() {
    if (!invite) {
      return
    }

    setAccepting(true)

    try {
      await apiFetch(`/companies/members/invites/${token}/accept`, {
        method: "POST",
      })
      // The bell hears the company just joined at once.
      window.dispatchEvent(new Event(COMPANIES_CHANGED))
      router.push("/companies")
    } catch (error) {
      const forbidden = error instanceof ApiError && error.status === 403
      toast.error(forbidden ? share("wrongEmail") : share("acceptFailed"))
      setAccepting(false)
    }
  }

  if (status !== "ready" || !invite) {
    return (
      <LinkStatus
        status={status === "ready" ? "loading" : status}
        invalid={share("invalid")}
        onRetry={retry}
      />
    )
  }

  // The backend says whether the invite is this account's.
  const matches = invite.matches ?? false

  return (
    <div className="w-full space-y-8 text-center">
      <div className="space-y-4">
        <p className="text-base text-muted-foreground">
          {invite.company_id ? share("joined") : share("invitedToJoin")}
        </p>
        <h1 className="font-heading text-4xl font-medium tracking-tight text-balance normal-case sm:text-5xl">
          {invite.company_name}
        </h1>
      </div>
      {!user ? (
        <Button className="h-12 px-6 text-base" onClick={() => signIn()}>
          {t("signInToJoin")}
        </Button>
      ) : invite.company_id ? (
        <Button
          className="h-12 px-6 text-base"
          onClick={() =>
            router.push(`/companies/${invite.company_id}/interviews`)
          }
        >
          {t("open")}
        </Button>
      ) : invite.joined ? (
        // Used by someone else, or by this email from another account.
        <InfoCard className="mx-auto w-fit text-start">
          {share("used")}
        </InfoCard>
      ) : matches ? (
        <Button
          className="h-12 px-6 text-base"
          disabled={accepting}
          onClick={accept}
        >
          {t("join")}
        </Button>
      ) : (
        // Signed in with another email: a warning, in the warning card.
        <WarningCard className="mx-auto w-fit text-start">
          {share("mismatch")}
        </WarningCard>
      )}
    </div>
  )
}
