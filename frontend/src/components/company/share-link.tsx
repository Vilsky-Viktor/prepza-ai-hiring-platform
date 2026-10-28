"use client"

import { cn } from "cn"
import { LinkIcon } from "lucide-react"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { CopyField } from "@/components/copy-field"
import { CornerSign } from "@/components/corner-sign"
import { Switch } from "@/components/ui/switch"
import { SIGN_CARD } from "@/config/cards"
import { apiErrorMessage, apiFetch } from "@/lib/api"

/** One link for many candidates, for a job ad: on or off, and the link to copy while it's on.
 * Without `canEdit` (a viewer) the switch only shows whether it's on. */
export function ShareLink({
  interviewId,
  linkToken,
  canEdit,
}: {
  interviewId: string
  linkToken: string | null
  canEdit: boolean
}) {
  const t = useTranslations("interviews")
  const router = useRouter()
  const [token, setToken] = useState(linkToken)
  const [saving, setSaving] = useState(false)

  async function toggle(on: boolean) {
    setSaving(true)

    try {
      const saved = await apiFetch<{ link_token: string | null }>(
        `/companies/interviews/${interviewId}/link`,
        { method: "PUT", body: JSON.stringify({ on }) }
      )
      setToken(saved.link_token)
      router.refresh()
    } catch (error) {
      toast.error(apiErrorMessage(error, t("linkFailed")))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={cn(SIGN_CARD, "space-y-4")}>
      <CornerSign>
        <LinkIcon className="text-primary" />
      </CornerSign>
      <label className="flex cursor-pointer items-center gap-4 text-base">
        <span className="min-w-0 flex-1 space-y-1">
          <span className="block font-medium lowercase">{t("linkTitle")}</span>
          <span className="block text-sm text-muted-foreground">
            {t("linkText")}
          </span>
        </span>
        <Switch
          checked={token !== null}
          disabled={saving || !canEdit}
          onCheckedChange={toggle}
        />
      </label>
      {token && <CopyField path={`/apply/${token}`} />}
    </div>
  )
}
