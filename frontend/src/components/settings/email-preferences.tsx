"use client"

import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { Checkbox } from "@/components/ui/checkbox"
import { DIGEST_KINDS, OTHER_EMAILS } from "@/constants/emails"
import { apiErrorMessage } from "@/lib/api"
import { saveEmailPreferences } from "@/lib/emails"
import type { EmailChanges, EmailPreferences } from "@/types/emails"
import { LIST_BOX } from "@/constants/lists"

// The size of the Slack kinds' and the interview settings' checkboxes.
const BIG = "size-7 shrink-0 [&_[data-slot=checkbox-indicator]>svg]:size-5"

/** Which emails the user gets beyond service emails; each change is saved at once, as the user's
 * own unless `onSave` saves it another way (a superadmin's, in the admin zone). */
export function EmailPreferencesSetting({
  initial,
  onSave = (changes) => saveEmailPreferences(changes, "settings"),
}: {
  initial: EmailPreferences
  onSave?: (changes: EmailChanges) => Promise<EmailPreferences>
}) {
  const t = useTranslations("settings.emails")
  const [saved, setSaved] = useState(initial)
  const [saving, setSaving] = useState(false)

  async function save(changes: EmailChanges) {
    setSaving(true)

    try {
      setSaved(await onSave(changes))
    } catch (error) {
      toast.error(apiErrorMessage(error, t("failed")))
    } finally {
      setSaving(false)
    }
  }

  // One block per kind of email, in a list like the Slack notification kinds: a checkbox, a
  // title and a note; the digest's own kinds sit under its title, smaller.
  function block(
    checkbox: React.ReactNode,
    title: string,
    note: string,
    className = ""
  ) {
    return (
      <label className={`flex cursor-pointer items-start gap-4 ${className}`}>
        {checkbox}
        <span className="space-y-1">
          <span className="block text-lg font-light">{title}</span>
          <span className="block text-sm text-muted-foreground">{note}</span>
        </span>
      </label>
    )
  }

  const digestOn = DIGEST_KINDS.filter((kind) => saved[kind]).length

  return (
    <div className="space-y-4">
      <div className={LIST_BOX} data-testid="email-preferences">
        <div className="space-y-4 p-4 sm:p-6">
          {block(
            // Turns every kind on or off at once; a dash when only some are on.
            <Checkbox
              className={BIG}
              checked={digestOn === DIGEST_KINDS.length}
              indeterminate={digestOn > 0 && digestOn < DIGEST_KINDS.length}
              disabled={saving}
              onCheckedChange={(on) =>
                save(Object.fromEntries(DIGEST_KINDS.map((kind) => [kind, on])))
              }
            />,
            t("digest"),
            t("digestNote")
          )}
          {/* Lined up with the digest's title. */}
          <div className="space-y-3 ps-11">
            {DIGEST_KINDS.map((kind) => (
              <label
                key={kind}
                className="flex cursor-pointer items-center gap-3 text-base font-light text-muted-foreground"
              >
                <Checkbox
                  className="size-6 shrink-0 [&_[data-slot=checkbox-indicator]>svg]:size-4"
                  checked={saved[kind]}
                  disabled={saving}
                  onCheckedChange={(on) => save({ [kind]: on })}
                />
                {t(`kinds.${kind}`)}
              </label>
            ))}
          </div>
        </div>
        {OTHER_EMAILS.map((setting) => (
          <div key={setting}>
            {block(
              <Checkbox
                className={BIG}
                checked={saved[setting]}
                disabled={saving}
                onCheckedChange={(on) => save({ [setting]: on })}
              />,
              t(setting),
              t(`${setting}Note`),
              "p-4 sm:p-6"
            )}
          </div>
        ))}
      </div>
      <p className="text-sm text-muted-foreground">{t("alwaysSent")}</p>
    </div>
  )
}
