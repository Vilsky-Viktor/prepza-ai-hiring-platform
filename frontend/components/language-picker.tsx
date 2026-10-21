"use client"

import { useTranslations } from "next-intl"

import { SearchPicker } from "@/components/search-picker"
import { LANGUAGE_NAMES, type Locale } from "@/constants/i18n"

/** A dropdown of languages with a search field, each named in its own language. `compact` is
 * the small trigger that sits next to a text box's send button. */
export function LanguagePicker({
  languages,
  value,
  onChange,
  label,
  disabled = false,
  compact = false,
}: {
  languages: readonly Locale[]
  value: Locale
  onChange: (language: Locale) => void
  label: string
  disabled?: boolean
  compact?: boolean
}) {
  const t = useTranslations("settings")

  return (
    <SearchPicker
      items={languages}
      value={value}
      onChange={onChange}
      labelOf={(language) => LANGUAGE_NAMES[language]}
      label={label}
      placeholder={t("searchLanguage")}
      empty={t("noLanguage")}
      disabled={disabled}
      compact={compact}
    />
  )
}
