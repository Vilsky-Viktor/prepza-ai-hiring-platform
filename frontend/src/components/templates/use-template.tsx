"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import type { Interview } from "@/types/company"

/** Copies the template into the company's own test, free and ready at once, and opens it. */
export function UseTemplate({
  templateId,
  companyId,
}: {
  templateId: string
  companyId: string
}) {
  const t = useTranslations("templates")
  const router = useRouter()
  const [busy, setBusy] = useState(false)

  async function use() {
    setBusy(true)

    try {
      const interview = await apiFetch<Interview>(
        `/companies/interviews/from-template?company_id=${companyId}`,
        { method: "POST", body: JSON.stringify({ template_id: templateId }) }
      )
      router.push(`/companies/${companyId}/interviews/${interview.id}`)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("useFailed")))
      setBusy(false)
    }
  }

  return (
    <Button
      variant="outline"
      className="h-10 shrink-0 px-5 text-base"
      disabled={busy}
      onClick={use}
      data-testid="use-template"
    >
      {busy ? t("using") : t("use")}
    </Button>
  )
}
