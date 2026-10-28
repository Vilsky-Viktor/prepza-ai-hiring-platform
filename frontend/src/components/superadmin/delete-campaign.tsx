"use client"

import { Trash2Icon } from "lucide-react"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { ConfirmDialog } from "@/components/common/confirm-dialog"
import { Button } from "@/components/ui/button"
import { apiErrorMessage, apiFetch } from "@/lib/api"

/** A draft campaign's delete button, on its title's line as a template's: asks first, then
 * goes back to the list. The API refuses a campaign that's no longer a draft and says why. */
export function DeleteCampaign({ campaignId }: { campaignId: string }) {
  const t = useTranslations("superadmin")
  const common = useTranslations("common")
  const router = useRouter()
  const [asking, setAsking] = useState(false)
  const [busy, setBusy] = useState(false)

  async function remove() {
    setBusy(true)

    try {
      await apiFetch(`/notifications/superadmin/campaigns/${campaignId}`, {
        method: "DELETE",
      })
      router.push("/superadmin/campaigns")
    } catch (error) {
      toast.error(apiErrorMessage(error, t("actionFailed")))
      setBusy(false)
    }
  }

  return (
    <>
      <Button
        variant="ghost"
        size="icon"
        className="size-12 shrink-0 text-muted-foreground hover:text-destructive"
        aria-label={t("deleteCampaign")}
        tooltip={common("delete")}
        onClick={() => setAsking(true)}
        data-testid="delete-campaign"
      >
        <Trash2Icon className="size-6" />
      </Button>
      <ConfirmDialog
        open={asking}
        onOpenChange={(open) => !busy && setAsking(open)}
        title={t("campaignConfirm.delete.title")}
        text={t("campaignConfirm.delete.text")}
        confirm={t("campaignConfirm.delete.confirm")}
        busy={busy}
        onConfirm={remove}
      />
    </>
  )
}
