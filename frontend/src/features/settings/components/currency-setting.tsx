"use client"

import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { CurrencySelect } from "@/components/common/currency-select"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import type { CurrencyChoice } from "@/types/billing"

/** The currency prices show in outside a company's billing, saved right away. */
export function CurrencySetting({ initial }: { initial: CurrencyChoice }) {
  const t = useTranslations("settings")
  const [currency, setCurrency] = useState(initial.currency)
  const [saving, setSaving] = useState(false)

  async function choose(next: string) {
    const before = currency
    setCurrency(next as CurrencyChoice["currency"])
    setSaving(true)

    try {
      await apiFetch("/billing/me/currency", {
        method: "PUT",
        body: JSON.stringify({ currency: next }),
      })
    } catch (error) {
      setCurrency(before)
      toast.error(apiErrorMessage(error, t("currencyFailed")))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div data-testid="user-currency" data-currency={currency}>
      <CurrencySelect
        label={t("currency")}
        value={currency}
        currencies={initial.currencies}
        onChange={choose}
        disabled={saving}
      />
    </div>
  )
}
