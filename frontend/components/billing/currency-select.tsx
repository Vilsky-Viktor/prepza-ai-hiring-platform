"use client"

import { useLocale } from "next-intl"

import { PillSelect } from "@/components/pill-select"

/** A choice of the currencies billing offers, each by its name in the page's language and its
 * code ("Euro (EUR)"). */
export function CurrencySelect({
  label,
  value,
  currencies,
  onChange,
  disabled,
}: {
  label: string
  value: string
  currencies: string[]
  onChange: (currency: string) => void
  disabled?: boolean
}) {
  const locale = useLocale()
  const names = new Intl.DisplayNames(locale, { type: "currency" })

  return (
    <PillSelect
      ariaLabel={label}
      pillClassName="h-12 max-w-xs px-5 pe-14 text-base [&>svg]:end-5 [&>svg]:size-5"
      value={value}
      onChange={onChange}
      disabled={disabled}
      options={currencies.map((currency) => ({
        value: currency,
        label: `${names.of(currency) ?? currency} (${currency})`,
      }))}
    />
  )
}
