"use client"

import { useTranslations } from "next-intl"
import { useEffect, useState } from "react"
import { toast } from "sonner"

import { CurrencySelect } from "@/components/billing/currency-select"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import type { CompanyCurrency } from "@/types/billing"

/** The currency the company's top-ups are priced and paid in, wherever the buyer is, as a small
 * pill beside its Top up button: owners and admins change it (saved at once), others see the
 * code. Automatic top-up follows it too. Read in the browser, so billing sees the visitor's country for a company with none saved yet. */
export function CompanyCurrencySetting({
  companyId,
  canEdit,
}: {
  companyId: string
  canEdit: boolean
}) {
  const t = useTranslations("companyBilling")
  const path = `/companies/companies/${companyId}/billing/currency`
  const [setting, setSetting] = useState<CompanyCurrency | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    apiFetch<CompanyCurrency>(path)
      .then(setSetting)
      .catch(() => {})
  }, [path])

  if (!setting) {
    return null
  }

  async function choose(currency: string) {
    setSaving(true)

    try {
      setSetting(
        await apiFetch<CompanyCurrency>(path, {
          method: "PUT",
          body: JSON.stringify({ currency }),
        })
      )
    } catch (error) {
      toast.error(apiErrorMessage(error, t("currencyFailed")))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div data-testid="company-currency" data-currency={setting.currency}>
      {canEdit ? (
        <CurrencySelect
          label={t("currency")}
          value={setting.currency}
          currencies={setting.currencies}
          onChange={choose}
          disabled={saving}
          triggerClassName="h-10 w-auto max-w-none gap-2 px-5"
          short
        />
      ) : (
        <span className="text-sm text-muted-foreground">
          {setting.currency}
        </span>
      )}
    </div>
  )
}
