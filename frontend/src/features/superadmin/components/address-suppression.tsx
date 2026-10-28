"use client"

import { useLocale, useTranslations } from "next-intl"
import { useEffect, useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { WarningCard } from "@/components/common/warning-card"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { formatDate } from "@/lib/format"
import { hasMessage } from "@/lib/messages"
import { timeTag } from "@/lib/time-tag"
import type { components } from "@/types/api/notifications"

type Suppression = components["schemas"]["SuppressionOut"]

const PATH = "/notifications/superadmin/suppressed"

/** On an account's or a candidate's page, when the address is on prepza's suppression list
 * (it bounced, marked an email as spam, or Resend stopped sending to it): since when and why, as
 * a warning, and taking it off the list (Resend's too) so emails reach it again. Nothing while
 * it isn't on the list. The address goes in the body. */
export function AddressSuppression({ email }: { email: string }) {
  const t = useTranslations("superadmin")
  const locale = useLocale()
  const [found, setFound] = useState<Suppression | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    apiFetch<Suppression>(`${PATH}/lookup`, {
      method: "POST",
      body: JSON.stringify({ email }),
    })
      .then(setFound)
      .catch(() => {})
  }, [email])

  if (!found?.reason || !found.created_at) {
    return null
  }

  const reason = `suppressed.${found.reason}` as const

  async function remove() {
    setBusy(true)

    try {
      setFound(
        await apiFetch<Suppression>(`${PATH}/remove`, {
          method: "POST",
          body: JSON.stringify({ email }),
        })
      )
    } catch (error) {
      toast.error(apiErrorMessage(error, t("actionFailed")))
    } finally {
      setBusy(false)
    }
  }

  return (
    <WarningCard
      action={
        <Button
          variant="outline"
          className="h-10 px-5"
          disabled={busy}
          onClick={remove}
          data-testid="remove-suppression"
        >
          {t("removeSuppression")}
        </Button>
      }
    >
      {hasMessage(t, reason)
        ? t.rich(reason, {
            date: formatDate(found.created_at, locale),
            ...timeTag(found.created_at),
          })
        : found.reason}
    </WarningCard>
  )
}
