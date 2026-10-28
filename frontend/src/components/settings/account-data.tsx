"use client"

import { DownloadIcon, Trash2Icon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { DeleteAccount } from "@/components/delete-account"
import { Button } from "@/components/ui/button"
import { downloadMyData } from "@/lib/account"
import { apiErrorMessage } from "@/lib/api"

export function AccountData() {
  const t = useTranslations("settings")
  const [downloading, setDownloading] = useState(false)
  const [deleting, setDeleting] = useState(false)

  async function download() {
    setDownloading(true)

    try {
      await downloadMyData()
    } catch (error) {
      toast.error(apiErrorMessage(error, t("downloadFailed")))
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="flex flex-wrap gap-2">
      <Button
        variant="outline"
        className="h-10 px-5"
        disabled={downloading}
        onClick={download}
      >
        <DownloadIcon />
        {t("download")}
      </Button>
      <Button
        variant="outline"
        className="h-10 px-5 text-destructive hover:text-destructive"
        data-testid="delete-account"
        onClick={() => setDeleting(true)}
      >
        <Trash2Icon />
        {t("delete")}
      </Button>
      <DeleteAccount open={deleting} onOpenChange={setDeleting} />
    </div>
  )
}
