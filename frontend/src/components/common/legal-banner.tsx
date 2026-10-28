"use client"

import { XIcon } from "lucide-react"
import Link from "next/link"
import { useLocale, useTranslations } from "next-intl"
import { useEffect, useState } from "react"

import { useAuth } from "@/providers/auth-provider"
import { Button } from "@/components/ui/button"
import { InfoCard } from "@/components/common/warning-card"
import { apiFetch } from "@/lib/api"
import { formatDay } from "@/lib/format"
import { hasMessage } from "@/lib/messages"
import { notClosed, rememberClosed } from "@/lib/legal-banner"
import { timeTag } from "@/lib/time-tag"
import type { LegalChange } from "@/types/campaigns"

/** While a legal document's new version has been announced and doesn't apply yet, a thin
 * notice above the page says from when, with a link to it (the API says which concern the
 * user). Closing it keeps it closed in this browser for that version. As the maintenance
 * notice, it takes the page's top padding. */
export function LegalBanner() {
  const t = useTranslations("notifications")
  const locale = useLocale()
  const { user } = useAuth()
  const [changes, setChanges] = useState<LegalChange[]>([])

  useEffect(() => {
    if (!user) {
      return
    }

    apiFetch<LegalChange[]>("/notifications/me/legal-changes")
      .then((found) => setChanges(notClosed(found)))
      .catch(() => {})
  }, [user])

  if (!user || changes.length === 0) {
    return null
  }

  function close(change: LegalChange) {
    rememberClosed(change)
    setChanges((current) => current.filter((item) => item !== change))
  }

  return (
    // Above the page, which its negative margin lets overlap it, so its close button takes
    // clicks.
    <div
      data-testid="legal-banner"
      className="relative z-10 mx-auto -mb-8 max-w-page space-y-2 px-6 pt-6"
    >
      {changes.map((change) => {
        const key = `legalBanner.${change.document}` as const

        // A document the messages don't name has no notice.
        if (!hasMessage(t, key)) {
          return null
        }

        return (
          <InfoCard
            key={change.document}
            className="py-2 ps-5 pe-2 text-sm"
            action={
              <Button
                variant="ghost"
                size="icon"
                className="text-muted-foreground hover:text-foreground"
                aria-label={t("closeLegalBanner")}
                tooltip={t("closeLegalBanner")}
                onClick={() => close(change)}
              >
                <XIcon />
              </Button>
            }
          >
            {t.rich(key, {
              date: formatDay(change.version, locale),
              ...timeTag(change.version),
            })}{" "}
            <Link
              href={`/${change.document}`}
              className="font-medium text-foreground underline underline-offset-4"
            >
              {t("readLegal")}
            </Link>
          </InfoCard>
        )
      })}
    </div>
  )
}
