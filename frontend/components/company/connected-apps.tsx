"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { useLocalTime } from "@/hooks/use-local-time"
import { ConfirmDialog } from "@/components/confirm-dialog"
import { Button } from "@/components/ui/button"
import { Dot } from "@/components/dot"
import { LIST_BOX } from "@/constants/lists"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { bdi } from "@/lib/bidi"
import type { AiConnection } from "@/types/connections"

/** The AI apps the user connected to their account, in one list like the API keys: each with
 * its name, where it runs, when it was connected and last used, and Disconnect. */
export function ConnectedApps({
  connections,
}: {
  connections: AiConnection[]
}) {
  const t = useTranslations("aiApps")
  const localTime = useLocalTime()

  return (
    <section className="space-y-6">
      {connections.length ? (
        <ul className={LIST_BOX}>
          {connections.map((app) => (
            <li
              key={app.id}
              // On phones Disconnect goes on its own line, centered.
              className="flex items-center justify-between gap-4 p-6 max-sm:flex-col max-sm:items-stretch"
            >
              <span className="min-w-0 space-y-1">
                <span className="block text-lg font-medium break-all">
                  {app.client_name}
                </span>
                <span className="block text-sm text-muted-foreground">
                  {app.redirect_host}
                  <Dot />
                  <time suppressHydrationWarning>
                    {t("connectedOn", {
                      date: localTime.date(app.created_at),
                    })}
                  </time>
                  <Dot />
                  <time suppressHydrationWarning>
                    {app.last_used_at
                      ? t("lastUsed", {
                          date: localTime.date(app.last_used_at),
                        })
                      : t("neverUsed")}
                  </time>
                </span>
              </span>
              <span className="max-sm:flex max-sm:justify-center">
                <Disconnect app={app} />
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="rounded-2xl border p-6 text-muted-foreground">
          {t("noConnected")}
        </p>
      )}
    </section>
  )
}

/** Disconnect, after asking: the app's access ends at once. */
function Disconnect({ app }: { app: AiConnection }) {
  const t = useTranslations("aiApps")
  const ats = useTranslations("ats")
  const router = useRouter()
  const [confirming, setConfirming] = useState(false)
  const [busy, setBusy] = useState(false)

  async function disconnect() {
    setBusy(true)

    try {
      await apiFetch(`/assistant/connections/${app.id}`, { method: "DELETE" })
      setConfirming(false)
      router.refresh()
    } catch (error) {
      toast.error(apiErrorMessage(error, t("disconnectFailed")))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <Button
        variant="outline"
        className="h-10 shrink-0 px-5 text-base"
        disabled={busy}
        onClick={() => setConfirming(true)}
      >
        {ats("disconnect")}
      </Button>
      <ConfirmDialog
        open={confirming}
        onOpenChange={setConfirming}
        title={t.rich("disconnectTitle", { client: app.client_name, ...bdi })}
        text={t.rich("disconnectText", { client: app.client_name, ...bdi })}
        confirm={ats("disconnect")}
        busy={busy}
        onConfirm={disconnect}
      />
    </>
  )
}
