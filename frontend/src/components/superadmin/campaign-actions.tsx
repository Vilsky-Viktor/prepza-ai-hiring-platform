"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { ConfirmDialog } from "@/components/confirm-dialog"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { WarningCard } from "@/components/warning-card"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import type { Campaign } from "@/types/campaigns"

const BUTTON = "h-10 px-5 text-base"

/** Sending a campaign, beside its recipients: while it's a draft, send a test (in the language
 * shown) to oneself, or send it (after confirming with how many get it; an important notice
 * also after ticking that it's about the service, not a promotion); while it's going out, stop
 * it. Editing and deleting are on its title's line. The API refuses what's no longer allowed
 * and says why. */
export function CampaignActions({
  campaign,
  language,
  recipients,
  onChanged,
}: {
  campaign: Campaign
  language: string
  recipients: number | null
  onChanged: (campaign: Campaign) => void
}) {
  const t = useTranslations("superadmin")
  const router = useRouter()
  const [asking, setAsking] = useState<"send" | "stop" | null>(null)
  const [busy, setBusy] = useState(false)
  // An important notice's sender confirmed it isn't a promotion.
  const [acknowledged, setAcknowledged] = useState(false)
  // Sending an important notice: it asks more.
  const noticing = asking === "send" && campaign.kind === "notices"
  const path = `/notifications/superadmin/campaigns/${campaign.id}`

  async function act(run: () => Promise<void>) {
    setBusy(true)

    try {
      await run()
      setAsking(null)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("actionFailed")))
    } finally {
      setBusy(false)
    }
  }

  const sendTest = () =>
    act(async () => {
      await apiFetch(`${path}/test?language=${language}`, { method: "POST" })
      toast.success(t("testSent"))
    })

  const confirmed = () =>
    act(async () => {
      onChanged(
        await apiFetch<Campaign>(`${path}/${asking}`, {
          method: "POST",
          body:
            asking === "send" ? JSON.stringify({ acknowledged }) : undefined,
        })
      )
      router.refresh()
    })

  if (campaign.status === "sent" || campaign.status === "stopped") {
    return null
  }

  return (
    // On phones the two fill a line, 70/30.
    <div className="flex items-center gap-3 max-sm:w-full">
      {campaign.status === "draft" ? (
        <>
          <Button
            variant="outline"
            className={`${BUTTON} max-sm:flex-[7_1_0%]`}
            disabled={busy}
            onClick={sendTest}
            data-testid="send-test"
          >
            {t("sendTest")}
          </Button>
          <Button
            className={`${BUTTON} max-sm:flex-[3_1_0%]`}
            disabled={busy}
            onClick={() => setAsking("send")}
            data-testid="send-campaign"
          >
            {t("sendCampaign")}
          </Button>
        </>
      ) : (
        <Button
          variant="outline"
          className={BUTTON}
          onClick={() => setAsking("stop")}
          data-testid="stop-campaign"
        >
          {t("stopCampaign")}
        </Button>
      )}
      <ConfirmDialog
        open={asking !== null}
        onOpenChange={(open) => {
          if (!open) {
            setAsking(null)
            setAcknowledged(false)
          }
        }}
        title={
          asking
            ? t(`campaignConfirm.${noticing ? "notice" : asking}.title`)
            : ""
        }
        text={
          asking === "send" && recipients === null
            ? t("campaignConfirm.send.unknown")
            : asking
              ? t(`campaignConfirm.${asking}.text`, { count: recipients ?? 0 })
              : ""
        }
        confirm={asking ? t(`campaignConfirm.${asking}.confirm`) : ""}
        busy={busy}
        onConfirm={confirmed}
        confirmDisabled={noticing && !acknowledged}
      >
        {noticing && (
          <div className="space-y-4">
            <WarningCard>{t("campaignConfirm.notice.warning")}</WarningCard>
            <label className="flex cursor-pointer items-start gap-3 text-base">
              <Checkbox
                className="mt-0.5 size-6 shrink-0 [&_[data-slot=checkbox-indicator]>svg]:size-4"
                checked={acknowledged}
                onCheckedChange={(checked) => setAcknowledged(checked === true)}
                data-testid="notice-acknowledged"
              />
              {t("campaignConfirm.notice.acknowledge")}
            </label>
          </div>
        )}
      </ConfirmDialog>
    </div>
  )
}
