"use client"

import { useTranslations } from "next-intl"
import { useEffect, useState } from "react"
import { toast } from "sonner"

import { PillSelect } from "@/components/pill-select"
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
        <PillSelect
          ariaLabel={t("currency")}
          value={setting.currency}
          onChange={choose}
          disabled={saving}
          pillClassName="h-10 px-5 pe-11 text-base [&>svg]:end-3 [&>svg]:size-4"
          options={setting.currencies.map((currency) => ({
            value: currency,
            label: currency,
          }))}
        />
      ) : (
        <span className="text-sm text-muted-foreground">
          {setting.currency}
        </span>
      )}
    </div>
  )
}
