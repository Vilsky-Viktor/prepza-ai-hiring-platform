"use client"

import { HistoryIcon, SendIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { useLocalTime } from "@/hooks/use-local-time"
import { IconButton } from "@/components/common/icon-button"
import { RollSecret } from "@/components/company/webhook-secret"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { bdi } from "@/lib/bidi"
import type { ApiWebhook, WebhookAttempt } from "@/types/api-access"

/** A web hook's own actions on the API page: owners and admins send it a signed test event and
 * roll its signing secret; anyone sees its delivery log, its latest sends and how they went. */
export function WebhookActions({
  companyId,
  hook,
  canEdit,
}: {
  companyId: string
  hook: ApiWebhook
  canEdit: boolean
}) {
  const t = useTranslations("api")
  const path = `/v1/manage/webhooks/${hook.id}`
  const [testing, setTesting] = useState(false)

  async function test() {
    setTesting(true)

    try {
      const { ok } = await apiFetch<{ ok: boolean }>(
        `${path}/test?company_id=${companyId}`,
        { method: "POST" }
      )

      if (ok) {
        toast.success(t("testSent"))
      } else {
        toast.error(t("testNotTaken"))
      }
    } catch (error) {
      toast.error(apiErrorMessage(error, t("testFailed")))
    } finally {
      setTesting(false)
    }
  }

  return (
    <>
      {canEdit && (
        <IconButton label={t("sendTest")} disabled={testing} onClick={test}>
          <SendIcon className="size-6 rtl:-scale-x-100" />
        </IconButton>
      )}
      {canEdit && (
        <RollSecret path={`${path}/secret?company_id=${companyId}`} />
      )}
      <WebhookLog path={`${path}/log?company_id=${companyId}`} url={hook.url} />
    </>
  )
}

/** The delivery log, read when it opens: newest first. */
function WebhookLog({ path, url }: { path: string; url: string }) {
  const t = useTranslations("api")
  const common = useTranslations("common")
  const localTime = useLocalTime()
  const [open, setOpen] = useState(false)
  const [attempts, setAttempts] = useState<WebhookAttempt[] | null>(null)

  async function show() {
    setOpen(true)
    setAttempts(null)

    try {
      setAttempts(await apiFetch<WebhookAttempt[]>(path))
    } catch (error) {
      setOpen(false)
      toast.error(apiErrorMessage(error, t("logFailed")))
    }
  }

  function result(attempt: WebhookAttempt) {
    if (attempt.result === "delivered" || attempt.result === "skipped") {
      return t(`results.${attempt.result}`)
    }

    // Our key can't read its secret: nothing the company can fix, and retried once it's back.
    if (attempt.result === "secret unreadable") {
      return t("results.unreadable")
    }

    // The status the endpoint answered, or what went wrong on the way.
    return /^\d{3}$/.test(attempt.result)
      ? t("results.answered", { status: attempt.result })
      : t("results.error", { error: attempt.result })
  }

  return (
    <>
      <IconButton label={t("log")} onClick={show}>
        <HistoryIcon className="size-6" />
      </IconButton>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent showCloseButton={false} className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>{t("log")}</DialogTitle>
            <DialogDescription className="break-all">
              {t.rich("logText", { url, ...bdi })}
            </DialogDescription>
          </DialogHeader>
          {attempts?.length === 0 && (
            <p className="text-muted-foreground">{t("logEmpty")}</p>
          )}
          {!!attempts?.length && (
            <ul className="max-h-96 divide-y overflow-y-auto rounded-xl border">
              {attempts.map((attempt, index) => (
                <li
                  key={index}
                  className="flex items-baseline justify-between gap-4 px-4 py-3"
                >
                  <span className="min-w-0 space-y-0.5">
                    <span className="block font-mono text-sm break-all">
                      {attempt.event_type}
                    </span>
                    <time
                      suppressHydrationWarning
                      className="block text-sm text-muted-foreground"
                    >
                      {localTime.dateTime(attempt.at)}
                    </time>
                  </span>
                  <span
                    className={
                      attempt.ok
                        ? "shrink-0 text-sm text-muted-foreground"
                        : "shrink-0 text-sm text-destructive"
                    }
                  >
                    {result(attempt)}
                  </span>
                </li>
              ))}
            </ul>
          )}
          <DialogFooter>
            <DialogClose render={<Button className="h-10 px-5 text-base" />}>
              {common("close")}
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
