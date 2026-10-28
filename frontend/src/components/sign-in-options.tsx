"use client"

import { useTranslations } from "next-intl"
import { useState, useSyncExternalStore } from "react"
import { toast } from "sonner"

import { LegalConsent } from "@/components/legal-consent"
import { LinkedInIcon } from "@/components/brand-icons"
import { GitHubIcon, GoogleIcon } from "@/components/sign-in-icons"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { SIGN_IN_PROVIDERS, SIGNED_IN_BEFORE_KEY } from "@/config/auth"
import { signIn } from "@/lib/auth"
import { saveEmailPreferences, signInEmailChanges } from "@/lib/emails"
import type { SignInProvider } from "@/types/sign-in"

const NAMES: Record<SignInProvider, string> = {
  google: "Google",
  linkedin: "LinkedIn",
  github: "GitHub",
}

const ICONS: Record<SignInProvider, () => React.ReactNode> = {
  google: GoogleIcon,
  linkedin: () => <LinkedInIcon className="size-5" />,
  github: GitHubIcon,
}

/** The ways to sign in, Google, LinkedIn or GitHub, one account per email whichever is used;
 * the sign-in dialog shows them, a page that only asks to sign in and the assistant's sign-in
 * card. `onSignedIn` runs once signed in. */
function subscribe() {
  return () => {}
}

function signedInBefore() {
  try {
    return localStorage.getItem(SIGNED_IN_BEFORE_KEY) !== null
  } catch {
    return false
  }
}

export function SignInOptions({
  onSignedIn,
  first,
}: {
  onSignedIn?: () => void
  // Shown first: the way the visitor asked the assistant for.
  first?: SignInProvider | null
}) {
  const t = useTranslations("signIn")
  const [busy, setBusy] = useState(false)
  // The way just tried, when its email already has an account under another way.
  const [linking, setLinking] = useState<SignInProvider | null>(null)
  // The product updates opt-out and the promotions opt-in, both unticked at first.
  const [emails, setEmails] = useState({ noUpdates: false, promotions: false })
  // Someone has signed in on this browser before: an existing account's email choices are in its
  // settings, so the card leaves them out.
  const returning = useSyncExternalStore(subscribe, signedInBefore, () => false)

  async function saveEmails() {
    try {
      await saveEmailPreferences(signInEmailChanges(emails), "sign_in")
    } catch {
      toast.error(t("emailsFailed"))
    }
  }

  async function choose(name: SignInProvider) {
    setBusy(true)
    const result = await signIn(name)

    const signedIn = ["done", "verify", "verifyFailed"].includes(result)

    if (!returning && signedIn) {
      await saveEmails()
    }

    setBusy(false)

    if (result === "done") {
      onSignedIn?.()
    } else if (result === "verify") {
      toast.info(t("verify"))
      onSignedIn?.()
    } else if (result === "verifyFailed") {
      toast.error(t("verifyFailed"))
      onSignedIn?.()
    } else if (result === "link") {
      setLinking(name)
    } else if (result === "failed") {
      toast.error(t("failed"))
    }
  }

  return (
    <div className="w-full space-y-4">
      {/* Only when the email already has an account under another way. */}
      {linking && (
        <p role="status" className="text-sm text-muted-foreground">
          {t("link", { provider: NAMES[linking] })}
        </p>
      )}
      <div className="space-y-3">
        {[
          ...SIGN_IN_PROVIDERS.filter((name) => name === first),
          ...SIGN_IN_PROVIDERS.filter((name) => name !== first),
        ]
          .filter((name) => name !== linking)
          .map((name) => {
            const Icon = ICONS[name]

            return (
              <Button
                key={name}
                variant="outline"
                className="h-12 w-full gap-3 text-base"
                disabled={busy}
                data-testid={`sign-in-${name}`}
                onClick={() => choose(name)}
              >
                <Icon />
                {/* One phrase, so each language puts the name where it belongs; the name keeps
                  its capitals inside the lowercase button. */}
                <span>
                  {t.rich("continueWith", {
                    provider: NAMES[name],
                    name: (chunks) => (
                      <span className="normal-case">{chunks}</span>
                    ),
                  })}
                </span>
              </Button>
            )
          })}
      </div>
      {/* Set a little apart from the buttons. */}
      <div className="space-y-4 pt-2">
        {!returning && (
          <div className="space-y-2">
            {(["noUpdates", "promotions"] as const).map((choice) => (
              <label
                key={choice}
                className="flex cursor-pointer items-center gap-3 text-sm"
              >
                <Checkbox
                  className="size-5 shrink-0 [&_[data-slot=checkbox-indicator]>svg]:size-3.5"
                  checked={emails[choice]}
                  disabled={busy}
                  data-testid={`email-box-${choice}`}
                  onCheckedChange={(checked) =>
                    setEmails({ ...emails, [choice]: checked })
                  }
                />
                {t(choice)}
              </label>
            ))}
          </div>
        )}
        <LegalConsent />
      </div>
    </div>
  )
}
