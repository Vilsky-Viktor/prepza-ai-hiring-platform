"use client"

import { DownloadIcon, Share2Icon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { ShareReport } from "@/components/company/share-report"
import { IconButton } from "@/components/icon-button"
import { reportPdf } from "@/lib/report-pdf"

/** Download a PDF report, or share it by email or chat. It's made from the hidden element
 * `reportId` (over several pages with `pages`), which `load`, when given, renders first;
 * `emailPath` emails it, `summary` is the chat message. Icons like the page's other actions; their tooltips name them. */
export function ReportActions({
  reportId,
  fileName,
  emailPath,
  summary,
  pages = false,
  load,
}: {
  reportId: string
  fileName: string
  emailPath: string
  summary: string
  pages?: boolean
  // Loads the report's data, and so the hidden report, the first time it's needed.
  load?: () => Promise<void>
}) {
  const t = useTranslations("report")
  const [busy, setBusy] = useState(false)
  const [sharing, setSharing] = useState(false)

  // Made from the hidden report on the page.
  async function makePdf() {
    const node = document.getElementById(reportId)

    return node ? reportPdf(node, `${fileName}.pdf`, pages) : null
  }

  async function download() {
    setBusy(true)

    try {
      await load?.()
      const file = await makePdf()

      if (file) {
        const url = URL.createObjectURL(file)
        const link = document.createElement("a")
        link.href = url
        link.download = file.name
        link.click()
        // Released once the browser has started saving it.
        setTimeout(() => URL.revokeObjectURL(url), 1000)
      }
    } catch {
      toast.error(t("failed"))
    } finally {
      setBusy(false)
    }
  }

  async function share() {
    setBusy(true)

    try {
      await load?.()
      setSharing(true)
    } catch {
      toast.error(t("failed"))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <IconButton label={t("download")} disabled={busy} onClick={download}>
        <DownloadIcon className="size-6" />
      </IconButton>
      <IconButton label={t("share")} disabled={busy} onClick={share}>
        <Share2Icon className="size-6" />
      </IconButton>
      <ShareReport
        open={sharing}
        onOpenChange={setSharing}
        path={emailPath}
        summary={summary}
        makePdf={makePdf}
      />
    </>
  )
}
