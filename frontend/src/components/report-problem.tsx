"use client"

import * as Sentry from "@sentry/nextjs"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

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
import { MAX_PROBLEM_REPORT_LENGTH } from "@/constants/limits"

/** "Report" on the error page: what the user was doing, sent to Sentry with the error it was
 * recorded as, so the description sits next to the page, browser and stack trace. */
export function ReportProblem() {
  const t = useTranslations("errors")
  const common = useTranslations("common")
  const [open, setOpen] = useState(false)
  const [message, setMessage] = useState("")

  function send(event: React.FormEvent) {
    event.preventDefault()
    Sentry.captureFeedback({
      message: message.trim(),
      // The error this page just recorded.
      associatedEventId: Sentry.lastEventId(),
    })
    setOpen(false)
    setMessage("")
    toast.success(t("reportSent"))
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={<Button variant="ghost" className="h-12 px-6 text-base" />}
        data-testid="report-problem"
      >
        {t("report")}
      </DialogTrigger>
      <DialogContent showCloseButton={false} className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("reportTitle")}</DialogTitle>
          <DialogDescription>{t("reportText")}</DialogDescription>
        </DialogHeader>
        <form id="report-problem" onSubmit={send}>
          <div className="relative rounded-xl border border-transparent transition-colors focus-within:border-ring-gradient">
            <Textarea
              required
              maxLength={MAX_PROBLEM_REPORT_LENGTH}
              placeholder={t("reportPlaceholder")}
              aria-label={t("reportPlaceholder")}
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              className="min-h-32 resize-none border-0 bg-surface px-6 py-4 text-lg shadow-none focus-visible:border-transparent focus-visible:ring-0 md:text-lg"
            />
          </div>
        </form>
        <DialogFooter>
          <DialogClose
            render={
              <Button variant="outline" className="h-10 px-5 text-base" />
            }
          >
            {common("cancel")}
          </DialogClose>
          <Button
            type="submit"
            form="report-problem"
            className="h-10 px-5 text-base"
            disabled={!message.trim()}
          >
            {t("reportSend")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
