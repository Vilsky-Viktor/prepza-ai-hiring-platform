"use client"

import { PauseIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { CornerSign } from "@/components/corner-sign"
import { Switch } from "@/components/ui/switch"
import { SIGN_CARD } from "@/constants/cards"
import { apiErrorMessage, apiFetch } from "@/lib/api"

/** The emergency pause, as the share link's switch: while on, every service refuses new
 * candidate interviews, practice rounds, previews and AI generation. */
export function PauseSwitch({ paused }: { paused: boolean }) {
  const t = useTranslations("superadmin")
  const [on, setOn] = useState(paused)
  const [saving, setSaving] = useState(false)

  async function toggle(next: boolean) {
    setSaving(true)

    try {
      const saved = await apiFetch<{ paused: boolean }>(
        "/companies/superadmin/pause",
        { method: "PUT", body: JSON.stringify({ paused: next }) }
      )
      setOn(saved.paused)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("pauseFailed")))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={SIGN_CARD}>
      <CornerSign>
        <PauseIcon className="text-primary" />
      </CornerSign>
      <label className="flex cursor-pointer items-center gap-4 text-base">
        <span className="min-w-0 flex-1 space-y-1">
          <span className="block font-medium">{t("pauseTitle")}</span>
          <span className="block text-sm text-muted-foreground">
            {t("pauseText")}
          </span>
        </span>
        <Switch checked={on} disabled={saving} onCheckedChange={toggle} />
      </label>
    </div>
  )
}
