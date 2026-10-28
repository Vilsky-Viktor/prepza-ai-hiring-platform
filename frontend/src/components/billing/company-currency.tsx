"use client"

import { useLocale, useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { CurrencySelect } from "@/components/billing/currency-select"
import { BILLING_REFRESHED } from "@/config/billing"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { formatPrice } from "@/lib/format"
import type { CompanyCurrency } from "@/types/billing"

/** The currency the company's top-ups are priced and paid in, wherever the buyer is, as a small
 * pill beside its Top up button: owners and admins change it (saved at once), others see the
 * code. Automatic top-up follows it too. Read by the page's server (`initial`), so it's there
 * as the page shows and nothing beside it moves. */
export function CompanyCurrencySetting({
  companyId,
  canEdit,
  initial,
}: {
  companyId: string
  canEdit: boolean
  initial: CompanyCurrency
}) {
  const t = useTranslations("companyBilling")
  const autoTopUp = useTranslations("autoTopUp")
  const locale = useLocale()
  const path = `/companies/companies/${companyId}/billing/currency`
  const [setting, setSetting] = useState(initial)
  const [saving, setSaving] = useState(false)

  async function choose(currency: string) {
    setSaving(true)

    try {
      const chosen = await apiFetch<CompanyCurrency>(path, {
        method: "PUT",
        body: JSON.stringify({ currency }),
      })
      setSetting(chosen)
      // What reads its own billing data (the automatic top-up) reads it again, in the new
      // currency.
      window.dispatchEvent(new Event(BILLING_REFRESHED))

      // A running automatic top-up charges in it at once, at the price billing says.
      if (chosen.auto_top_up_price != null) {
        toast.success(
          autoTopUp("currencyApplied", {
            amount: formatPrice(
              chosen.auto_top_up_price,
              chosen.currency,
              locale
            ),
          })
        )
      }
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
