"use client"

import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { Checkbox } from "@/components/ui/checkbox"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { hasMessage } from "@/lib/messages"
import { CARD_PADDING } from "@/config/cards"

/** Which of the company's notifications go to its Slack channel, one row each in a list like the
 * interview's settings; each change is saved at once. Viewers see them without changing. */
export function SlackKinds({
  companyId,
  kinds,
  allKinds,
  canEdit,
}: {
  companyId: string
  kinds: string[]
  allKinds: string[]
  canEdit: boolean
}) {
  const t = useTranslations("slack")
  const [chosen, setChosen] = useState(kinds)
  const [saving, setSaving] = useState(false)

  // A kind from the API by its name, or as it is when there's none.
  function named(kind: string) {
    const key = `kinds.${kind}` as const

    return hasMessage(t, key) ? t(key) : kind
  }

  async function toggle(kind: string, on: boolean) {
    const next = on
      ? allKinds.filter((item) => item === kind || chosen.includes(item))
      : chosen.filter((item) => item !== kind)
    setSaving(true)

    try {
      await apiFetch(`/notifications/slack/kinds?company_id=${companyId}`, {
        method: "PUT",
        body: JSON.stringify({ kinds: next }),
      })
      setChosen(next)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("saveFailed")))
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="space-y-6">
      <div className="space-y-1">
        <h2 className="font-heading text-2xl font-medium">{t("kindsTitle")}</h2>
        <p className="text-base text-muted-foreground">{t("kindsText")}</p>
      </div>
      <div className="divide-y rounded-xl border">
        {allKinds.map((kind) => (
          <label
            key={kind}
            className={`flex cursor-pointer items-center justify-between gap-4 ${CARD_PADDING}`}
          >
            <span className="text-lg font-light">{named(kind)}</span>
            <Checkbox
              className="size-7 shrink-0 [&_[data-slot=checkbox-indicator]>svg]:size-5"
              checked={chosen.includes(kind)}
              disabled={saving || !canEdit}
              onCheckedChange={(checked) => toggle(kind, checked)}
            />
          </label>
        ))}
      </div>
    </section>
  )
}
