"use client"

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
import { DayField } from "@/features/company/components/action-filters"
import { InterviewPicker } from "@/features/company/components/interview-picker"
import { apiErrorMessage } from "@/lib/api"
import { downloadFile } from "@/lib/download"
import { dayStart } from "@/lib/format"
import type { Interview } from "@/types/company"

// "All interviews" in the picker.
const ALL = "all"

/** The owner's export for an independent bias audit: the company's or one interview's finished
 * candidates, from and to a day when chosen, as a CSV file the API makes. */
export function BiasAuditExport({
  companyId,
  interviews,
}: {
  companyId: string
  interviews: Interview[]
}) {
  const t = useTranslations("biasAudit")
  const log = useTranslations("actionLog")
  const common = useTranslations("common")
  const [open, setOpen] = useState(false)
  const [interview, setInterview] = useState(ALL)
  const [from, setFrom] = useState("")
  const [to, setTo] = useState("")
  const [busy, setBusy] = useState(false)

  async function save(event: React.FormEvent) {
    event.preventDefault()
    setBusy(true)
    const params = new URLSearchParams()

    if (interview !== ALL) {
      params.set("interview_id", interview)
    }

    if (from) {
      params.set("from", dayStart(from))
    }

    if (to) {
      params.set("to", dayStart(to, 1))
    }

    try {
      await downloadFile(
        `/companies/companies/${companyId}/bias-audit?${params}`
      )
      setOpen(false)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("failed")))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !busy && setOpen(next)}>
      <DialogTrigger
        data-testid="bias-audit-export"
        render={<Button variant="outline" className="h-12 px-6 text-base" />}
      >
        {t("open")}
      </DialogTrigger>
      <DialogContent showCloseButton={false} className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{t("title")}</DialogTitle>
          <DialogDescription>{t("description")}</DialogDescription>
          <DialogDescription>{t("privacy")}</DialogDescription>
        </DialogHeader>
        <form id="bias-audit-form" className="space-y-4" onSubmit={save}>
          <InterviewPicker
            companyId={companyId}
            interviews={interviews}
            first={{ value: ALL, label: t("allInterviews") }}
            label={t("interview")}
            value={interview}
            onChange={setInterview}
            disabled={busy}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <DayField label={log("from")} value={from} onChange={setFrom} />
            <DayField label={log("to")} value={to} onChange={setTo} />
          </div>
        </form>
        <DialogFooter>
          <DialogClose
            render={
              <Button
                variant="outline"
                className="h-10 px-5 text-base"
                disabled={busy}
              />
            }
          >
            {common("cancel")}
          </DialogClose>
          <Button
            type="submit"
            form="bias-audit-form"
            className="h-10 px-5 text-base"
            disabled={busy}
          >
            {t("download")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
