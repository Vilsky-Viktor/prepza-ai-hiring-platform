"use client"

import { useLocale, useTranslations } from "next-intl"

import { SearchPicker } from "@/components/search-picker"

/** A choice of the currencies billing offers, with a search field, each by its name in the
 * page's language and its code ("Japanese Yen (JPY)"), so "yen", "JPY" or "円" finds it;
 * sorted by those names as the language sorts. `triggerClassName` sizes the trigger to sit
 * beside other controls. */
export function CurrencySelect({
  label,
  value,
  currencies,
  onChange,
  disabled,
  triggerClassName,
  short,
}: {
  label: string
  value: string
  currencies: string[]
  onChange: (currency: string) => void
  disabled?: boolean
  triggerClassName?: string
  // The trigger shows the code only (the list still names each).
  short?: boolean
}) {
  const t = useTranslations("settings")
  const locale = useLocale()
  const names = new Intl.DisplayNames(locale, { type: "currency" })
  const nameOf = (currency: string) =>
    `${names.of(currency) ?? currency} (${currency})`
  const collator = new Intl.Collator(locale)
  const sorted = [...currencies].sort((a, b) =>
    collator.compare(nameOf(a), nameOf(b))
  )

  return (
    <SearchPicker
      items={sorted}
      value={value}
      onChange={onChange}
      labelOf={nameOf}
      label={label}
      placeholder={t("searchCurrency")}
      empty={t("noCurrency")}
      disabled={disabled}
      triggerClassName={triggerClassName}
      valueLabel={short ? (currency) => currency : undefined}
    />
  )
}
