"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { CandidateFlow } from "@/components/company/ats-candidate-flow"
import { ConnectAts } from "@/components/company/ats-connect"
import { AtsWebhook } from "@/components/company/ats-webhook"
import { IntegrationRow } from "@/components/company/integration-row"
import { ConfirmDialog } from "@/components/confirm-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { WEBHOOKS, type AtsProvider } from "@/config/ats"
import { INTEGRATION_ACTIONS } from "@/config/lists"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import type { AtsConnection } from "@/types/company"

/** An ATS's row on the integrations tab: its logo, name and whether it's connected, laid out
 * like the companies list; the row opens the ATS's page (its linked jobs), its buttons sit on
 * top. */
export function AtsConnectionRow({
  companyId,
  companyName,
  provider,
  connection,
  canEdit,
}: {
  companyId: string
  companyName: string
  provider: AtsProvider
  connection: AtsConnection | null
  canEdit: boolean
}) {
  return (
    <IntegrationRow
      href={`/companies/${companyId}/integrations/${provider.id}`}
      logo={
        // The ATS's own icon (public/ats), as the companies list shows a logo.
        // eslint-disable-next-line @next/next/no-img-element
        <img src={provider.logo} alt="" className="size-full object-contain" />
      }
      name={provider.name}
      status={<AtsStatus connection={connection} />}
      text={
        connection && (
          <AtsAccount connection={connection} companyName={companyName} />
        )
      }
      actions={
        <AtsActions
          companyId={companyId}
          provider={provider}
          connection={connection}
          canEdit={canEdit}
        />
      }
    />
  )
}

/** What the company is connected as: its account in the ATS or, where the ATS names none
 * (Greenhouse), the company's own name; nothing before it's connected. */
export function AtsAccount({
  connection,
  companyName,
  className,
}: {
  connection: AtsConnection | null
  companyName: string
  className?: string
}) {
  if (!connection) {
    return null
  }

  return <span className={className}>{connection.account || companyName}</span>
}

/** "connected" beside the ATS's name once it is, like an interview's status tag; nothing
 * otherwise (Connect or Reconnect says the rest). */
export function AtsStatus({
  connection,
}: {
  connection: AtsConnection | null
}) {
  const t = useTranslations("ats")

  if (connection?.status !== "connected") {
    return null
  }

  return (
    <Badge className="h-7 shrink-0 px-3 text-sm font-light">
      {t("statusConnected")}
    </Badge>
  )
}

/** An ATS's buttons, on its row and its page: how candidates flow, and for owners and admins
 * Connect (or Reconnect when its key stopped working) and Disconnect. Greenhouse's and
 * Teamtailor's web hooks are set up by hand: their steps are in the info dialog, which opens
 * once it's connected. */
export function AtsActions({
  companyId,
  provider,
  connection,
  canEdit,
}: {
  companyId: string
  provider: AtsProvider
  connection: AtsConnection | null
  canEdit: boolean
}) {
  const t = useTranslations("ats")
  const router = useRouter()
  const [confirming, setConfirming] = useState(false)
  const [busy, setBusy] = useState(false)
  const [info, setInfo] = useState(false)
  const broken = connection?.status === "broken"
  const hooked = provider.id in WEBHOOKS

  async function disconnect() {
    setBusy(true)

    try {
      await apiFetch(`/ats/${provider.id}?company_id=${companyId}`, {
        method: "DELETE",
      })
      setConfirming(false)
      router.refresh()
    } catch (error) {
      toast.error(
        apiErrorMessage(error, t("disconnectFailed", { ats: provider.name }))
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <span className={INTEGRATION_ACTIONS} data-testid="integration-actions">
      <CandidateFlow provider={provider} open={info} onOpenChange={setInfo}>
        {canEdit && hooked && connection?.status === "connected" && (
          <AtsWebhook
            companyId={companyId}
            provider={provider as AtsProvider & { id: keyof typeof WEBHOOKS }}
          />
        )}
      </CandidateFlow>
      {canEdit && connection && (
        <Button
          variant="outline"
          className="h-10 px-5 text-base"
          onClick={() => setConfirming(true)}
        >
          {t("disconnect")}
        </Button>
      )}
      {canEdit && (connection === null || broken) && (
        <ConnectAts
          companyId={companyId}
          provider={provider}
          again={broken}
          onConnected={() => hooked && setInfo(true)}
        />
      )}
      <ConfirmDialog
        open={confirming}
        onOpenChange={setConfirming}
        title={t("disconnectTitle", { ats: provider.name })}
        text={t("disconnectText")}
        confirm={t("disconnect")}
        busy={busy}
        onConfirm={disconnect}
      />
    </span>
  )
}
