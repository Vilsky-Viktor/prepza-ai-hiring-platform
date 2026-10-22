"use client"

import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { EmailPreferencesSetting } from "@/components/settings/email-preferences"
import { Button } from "@/components/ui/button"
import { apiErrorMessage } from "@/lib/api"
import { bdi } from "@/lib/bidi"
import { allOptionalEmailsOff, saveForUser } from "@/lib/superadmin-emails"
import type { EmailChanges } from "@/types/emails"
import type { EmailLookup } from "@/types/superadmin"

/** A section of the support user page: a heading and its note, without a card around it,
 * like the page's other sections. */
function Section({
  title,
  description,
  children,
}: {
  title: string
  description: React.ReactNode
  children?: React.ReactNode
}) {
  return (
    <section className="space-y-4">
      <div className="space-y-1">
        <h2 className="text-lg font-medium">{title}</h2>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      {children}
    </section>
  )
}

/** The account's email settings, as Settings → Emails shows them, changed on the user's behalf:
 * the API logs each change as the superadmin's. */
export function AccountEmails({
  account,
}: {
  account: EmailLookup["account"]
}) {
  const t = useTranslations("superadmin")
  const [preferences, setPreferences] = useState(account?.preferences)
  // Shown again from what the API answered after every setting was turned off.
  const [shown, setShown] = useState(0)
  const [saving, setSaving] = useState(false)

  if (!account || !preferences) {
    return <Section title={t("account")} description={t("noAccount")} />
  }

  async function save(changes: EmailChanges) {
    const saved = await saveForUser(account!.user_id, changes)
    setPreferences(saved)

    return saved
  }

  async function turnOffAll() {
    setSaving(true)

    try {
      await save(allOptionalEmailsOff())
      setShown((count) => count + 1)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("actionFailed")))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Section
      title={t("account")}
      description={t.rich("accountText", { email: account.email, ...bdi })}
    >
      <EmailPreferencesSetting
        key={shown}
        initial={preferences}
        onSave={save}
      />
      <Button
        variant="outline"
        className="h-10 px-5"
        disabled={saving}
        onClick={turnOffAll}
        data-testid="turn-off-all"
      >
        {t("turnOffAll")}
      </Button>
    </Section>
  )
}
