"use client"

import { ScaleIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { ConfirmDialog } from "@/components/confirm-dialog"
import { Button } from "@/components/ui/button"
import { useAdminName } from "@/hooks/use-admin-name"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import type { LegalNotice } from "@/types/superadmin"

const PATH = "/notifications/superadmin/legal-notices"

/** The legal documents' notices, on the controls page as the switches' cards: a superadmin
 * decides a change is significant and has it emailed; the API says when that's possible (at
 * least 14 days before it applies, once per version) and who gets it. */
export function LegalNotices({ initial }: { initial: LegalNotice[] }) {
  const t = useTranslations("superadmin")
  const named = useAdminName()
  const [notices, setNotices] = useState(initial)
  const [asking, setAsking] = useState<LegalNotice>()
  const [busy, setBusy] = useState(false)

  async function send(notice: LegalNotice) {
    setBusy(true)

    try {
      await apiFetch(`${PATH}/${notice.document}`, { method: "POST" })
      setNotices(await apiFetch<LegalNotice[]>(PATH))
      toast.success(t("legalAsked"))
      setAsking(undefined)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("legalFailed")))
    } finally {
      setBusy(false)
    }
  }

  const name = (notice: LegalNotice) => named("legalDocuments", notice.document)

  return (
    <div className="space-y-4 rounded-2xl border p-5">
      <div className="flex items-center gap-4 text-base">
        <ScaleIcon aria-hidden className="size-7 shrink-0 text-primary" />
        <span className="min-w-0 flex-1 space-y-1">
          <span className="block font-medium">{t("legalTitle")}</span>
          <span className="block text-sm text-muted-foreground">
            {t("legalText")}
          </span>
        </span>
      </div>
      <ul className="divide-y" data-testid="legal-notices">
        {notices.map((notice) => (
          <li
            key={notice.document}
            className="flex flex-wrap items-center justify-between gap-3 py-5"
          >
            <span className="min-w-0 space-y-0.5">
              <span className="block">{name(notice)}</span>
              <span className="block text-sm text-muted-foreground">
                {t(`legalStates.${notice.state}`, { date: notice.version })}
              </span>
            </span>
            {notice.state === "sendable" && (
              <Button
                variant="outline"
                size="sm"
                className="h-8 px-3 text-sm"
                onClick={() => setAsking(notice)}
              >
                {t("legalSend")}
              </Button>
            )}
          </li>
        ))}
      </ul>
      {asking && (
        <ConfirmDialog
          open
          onOpenChange={(open) => !open && setAsking(undefined)}
          title={t("legalConfirmTitle", { document: name(asking) })}
          text={t(`legalAudience.${asking.audience}`, { date: asking.version })}
          confirm={t("legalSend")}
          busy={busy}
          onConfirm={() => send(asking)}
        />
      )}
    </div>
  )
}
