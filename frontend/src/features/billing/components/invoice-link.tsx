"use client"

import { DownloadIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { openAddress } from "@/lib/navigation"

/** Opens a top-up's invoice: its link is made on request and expires soon after. `api` is the
 * company's billing routes (its own, or the admin zone's support ones). */
export function InvoiceLink({
  api,
  transactionId,
}: {
  api: string
  transactionId: string
}) {
  const t = useTranslations("companyBilling")
  const [busy, setBusy] = useState(false)

  async function open() {
    setBusy(true)

    try {
      const { url } = await apiFetch<{ url: string }>(
        `${api}/invoice?transaction_id=${encodeURIComponent(transactionId)}`
      )
      openAddress(url)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("invoiceFailed")))
    } finally {
      setBusy(false)
    }
  }

  return (
    // An outline pill, like "set up automatic top-up".
    <Button
      type="button"
      variant="outline"
      size="sm"
      // The same padding on both sides: the button's own icon padding would cut the start's.
      className="h-8 gap-1.5 px-4 text-sm has-data-[icon=inline-start]:ps-4"
      onClick={open}
      disabled={busy}
    >
      <DownloadIcon data-icon="inline-start" />
      {t("invoice")}
    </Button>
  )
}
