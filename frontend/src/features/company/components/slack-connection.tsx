"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { IntegrationRow } from "@/features/company/components/integration-row"
import { ConfirmDialog } from "@/components/common/confirm-dialog"
import { InstructionsDialog } from "@/components/common/instructions-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Dotted } from "@/components/common/dot"
import { INTEGRATION_ACTIONS } from "@/config/lists"
import { SLACK } from "@/config/slack"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import type { SlackOverview } from "@/types/notifications"
import { openAddress } from "@/lib/navigation"

const STEPS = ["stepAdd", "stepChannel", "stepKinds", "stepPrivacy"] as const

/** Slack's row on the integrations tab, laid out like an ATS's: its mark, name, whether it's
 * connected and to which channel; the row opens Slack's page, its buttons sit on top. */
export function SlackRow({
  companyId,
  slack,
  canEdit,
}: {
  companyId: string
  slack: SlackOverview
  canEdit: boolean
}) {
  return (
    <IntegrationRow
      href={`/companies/${companyId}/integrations/slack`}
      logoClassName="p-6 max-sm:p-2"
      logo={
        // eslint-disable-next-line @next/next/no-img-element
        <img src={SLACK.logo} alt="" className="size-full object-contain" />
      }
      name={SLACK.name}
      status={<SlackStatus slack={slack} />}
      text={slack.connected && <Dotted items={[slack.team, slack.channel]} />}
      actions={
        <SlackActions companyId={companyId} slack={slack} canEdit={canEdit} />
      }
    />
  )
}

/** "connected" beside Slack's name once it works, like an ATS's tag; nothing otherwise. */
export function SlackStatus({ slack }: { slack: SlackOverview }) {
  const t = useTranslations("ats")

  if (slack.status !== "connected") {
    return null
  }

  return (
    <Badge className="h-7 shrink-0 px-3 text-sm font-light">
      {t("statusConnected")}
    </Badge>
  )
}

/** Slack's buttons, on its row and its page: its Instructions, and for owners and admins Add to
 * Slack (or Reconnect when Slack stopped taking messages), which goes to Slack to pick a channel
 * and comes back, and Disconnect. */
export function SlackActions({
  companyId,
  slack,
  canEdit,
}: {
  companyId: string
  slack: SlackOverview
  canEdit: boolean
}) {
  const t = useTranslations("slack")
  const ats = useTranslations("ats")
  const router = useRouter()
  const [confirming, setConfirming] = useState(false)
  const [busy, setBusy] = useState(false)

  async function connect() {
    setBusy(true)

    try {
      const { url } = await apiFetch<{ url: string }>(
        `/notifications/slack/start?company_id=${companyId}`
      )
      openAddress(url)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("connectFailed")))
      setBusy(false)
    }
  }

  async function disconnect() {
    setBusy(true)

    try {
      await apiFetch(`/notifications/slack?company_id=${companyId}`, {
        method: "DELETE",
      })
      setConfirming(false)
      router.refresh()
    } catch (error) {
      toast.error(apiErrorMessage(error, t("disconnectFailed")))
    } finally {
      setBusy(false)
    }
  }

  return (
    <span className={INTEGRATION_ACTIONS} data-testid="integration-actions">
      <InstructionsDialog
        title={t("instructionsTitle")}
        steps={STEPS.map((step) => t(step))}
      />
      {canEdit && slack.connected && (
        <Button
          variant="outline"
          className="h-10 px-5 text-base"
          onClick={() => setConfirming(true)}
        >
          {ats("disconnect")}
        </Button>
      )}
      {canEdit && (!slack.connected || slack.status !== "connected") && (
        <Button
          className="h-10 px-5 text-base"
          disabled={busy}
          onClick={connect}
        >
          {slack.connected ? ats("reconnect") : t("add")}
        </Button>
      )}
      <ConfirmDialog
        open={confirming}
        onOpenChange={setConfirming}
        title={t("disconnectTitle")}
        text={t("disconnectText")}
        confirm={ats("disconnect")}
        busy={busy}
        onConfirm={disconnect}
      />
    </span>
  )
}
