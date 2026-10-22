"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { MAX_DECLINE_REASON_LENGTH } from "@/constants/limits"
import { apiFetch } from "@/lib/api"
import { bdi } from "@/lib/bidi"
import { decisionFailed } from "@/lib/verification"

/** "Decline" on a pending verification: a confirm with an optional reason, which the company's
 * owners and admins see. */
export function DeclineVerification({
  companyId,
  name,
}: {
  companyId: string
  name: string
}) {
  const t = useTranslations("superadmin")
  const common = useTranslations("common")
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [reason, setReason] = useState("")
  const [sending, setSending] = useState(false)

  async function decline(event: React.FormEvent) {
    event.preventDefault()
    setSending(true)

    try {
      await apiFetch(
        `/companies/superadmin/verifications/${companyId}/decline`,
        {
          method: "POST",
          body: JSON.stringify({ reason: reason.trim() }),
        }
      )
      setOpen(false)
      router.refresh()
    } catch (error) {
      setOpen(false)
      decisionFailed(
        error,
        { changed: t("requestChanged"), failed: t("actionFailed") },
        router.refresh
      )
    } finally {
      setSending(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !sending && setOpen(next)}>
      <DialogTrigger
        render={
          <Button
            variant="destructive"
            size="sm"
            className="h-8 px-3 text-sm"
          />
        }
      >
        {t("decline")}
      </DialogTrigger>
      <DialogContent showCloseButton={false} className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="no-dot">
            {t.rich("declineTitle", { name, ...bdi })}
          </DialogTitle>
          <DialogDescription>{t("declineText")}</DialogDescription>
        </DialogHeader>
        <form id={`decline-${companyId}`} onSubmit={decline}>
          <div className="rounded-xl border border-transparent transition-colors focus-within:border-ring">
            <Textarea
              maxLength={MAX_DECLINE_REASON_LENGTH}
              placeholder={t("declineReason")}
              aria-label={t("declineReason")}
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              className="min-h-32 resize-none border-0 bg-muted px-6 py-4 text-lg shadow-none focus-visible:border-transparent focus-visible:ring-0 md:text-lg dark:bg-input/30"
            />
          </div>
        </form>
        <DialogFooter>
          <DialogClose
            render={
              <Button
                variant="outline"
                className="h-10 px-5 text-base"
                disabled={sending}
              />
            }
          >
            {common("cancel")}
          </DialogClose>
          <Button
            type="submit"
            form={`decline-${companyId}`}
            variant="destructive"
            className="h-10 px-5 text-base"
            disabled={sending}
          >
            {t("decline")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
