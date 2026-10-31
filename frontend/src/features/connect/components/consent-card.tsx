"use client"

import { cn } from "cn"
import { PencilLineIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { CornerSign } from "@/components/common/corner-sign"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { WarningCard } from "@/components/common/warning-card"
import { CARD, SIGN_CARD } from "@/config/cards"
import { ApiError, apiErrorMessage, apiFetch, serviceRefusal } from "@/lib/api"
import { bdi } from "@/lib/bidi"
import type { ConnectAnswer, ConnectRequest } from "@/types/connections"
import { openAddress } from "@/lib/navigation"

/** Asks the signed-in user whether an AI app may use their account: who asks, what it can and
 * can't do, whether it may make changes (on unless the app asked only to read), a warning for an
 * app testee doesn't know, and Deny or Allow; either answer goes back to the app. */
export function ConsentCard({
  requestId,
  request,
  email,
  onExpired,
}: {
  requestId: string
  request: ConnectRequest
  email: string
  // The request expired (10 minutes, signing in included) or was answered meanwhile.
  onExpired: () => void
}) {
  const t = useTranslations("connect")
  const common = useTranslations("common")
  const [busy, setBusy] = useState(false)
  const [changes, setChanges] = useState(!request.read_only)
  const client = request.client_name
  const can = [
    t("canRead"),
    ...(changes ? [t("canChange")] : []),
    t("canShare"),
  ]
  const cant = [
    ...(changes ? [] : [t("cantChange")]),
    t("cantSecrets"),
    t("cantDelete"),
  ]

  async function answer(choice: "approve" | "deny") {
    setBusy(true)

    try {
      const { redirect_url } = await apiFetch<ConnectAnswer>(
        `/assistant/connect/${encodeURIComponent(requestId)}/${choice}`,
        choice === "approve"
          ? { method: "POST", body: JSON.stringify({ read_only: !changes }) }
          : { method: "POST" }
      )
      openAddress(redirect_url)
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        onExpired()

        return
      }

      // Started in another browser: the API says to start again from the app.
      toast.error(
        serviceRefusal(error, [403]) ?? apiErrorMessage(error, common("failed"))
      )
      setBusy(false)
    }
  }

  return (
    <div className={`w-full max-w-md space-y-6 ${CARD}`}>
      <div className="space-y-3">
        <h1 className="font-heading text-3xl font-medium tracking-tight text-balance">
          {t.rich("title", {
            client,
            ...bdi,
            name: (chunks) => <span className="normal-case">{chunks}</span>,
          })}
        </h1>
        <p className="text-base break-words text-muted-foreground">
          {t.rich("who", {
            client,
            host: request.redirect_host,
            email,
            ...bdi,
          })}
        </p>
      </div>
      <List title={t("canTitle")} items={can} />
      <List title={t("cantTitle")} items={cant} />
      {!request.read_only && (
        <label
          className={cn(
            SIGN_CARD,
            "flex cursor-pointer items-center gap-4 text-base"
          )}
        >
          <CornerSign>
            <PencilLineIcon className="text-primary" />
          </CornerSign>
          <span className="min-w-0 flex-1 space-y-1">
            <span className="block font-medium lowercase">
              {t("changesTitle")}
            </span>
            <span className="block text-sm text-muted-foreground">
              {t("changesText")}
            </span>
          </span>
          <Switch
            checked={changes}
            disabled={busy}
            onCheckedChange={setChanges}
          />
        </label>
      )}
      {!request.known_client && <WarningCard>{t("unknown")}</WarningCard>}
      <div className="flex gap-3 max-sm:*:flex-1 sm:justify-end">
        <Button
          variant="outline"
          className="h-10 px-5 text-base"
          disabled={busy}
          onClick={() => answer("deny")}
        >
          {t("deny")}
        </Button>
        <Button
          className="h-10 px-5 text-base"
          disabled={busy}
          onClick={() => answer("approve")}
        >
          {t("allow")}
        </Button>
      </div>
      <p className="text-sm text-muted-foreground">{t("footnote")}</p>
    </div>
  )
}

function List({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="space-y-2">
      <h3 className="text-lg font-medium">{title}</h3>
      <ul className="list-disc space-y-1.5 ps-5 text-base text-muted-foreground">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  )
}
