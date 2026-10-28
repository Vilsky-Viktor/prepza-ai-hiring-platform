"use client"

import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { LanguagePicker } from "@/components/language-picker"
import { LOCALES, type Locale } from "@/constants/i18n"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { firebaseAuth } from "@/lib/firebase"

/** The interface language, saved right away. */
export function LanguageSetting({ current }: { current: Locale }) {
  const t = useTranslations("settings")
  const [saving, setSaving] = useState(false)

  async function choose(language: Locale) {
    setSaving(true)

    try {
      await apiFetch("/library/me/settings", {
        method: "PUT",
        body: JSON.stringify({ language }),
      })
      // The new token carries the language; auth-provider.tsx switches the interface to it.
      await (await firebaseAuth()).currentUser?.getIdToken(true)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("languageFailed")))
    } finally {
      setSaving(false)
    }
  }

  return (
    <LanguagePicker
      languages={LOCALES}
      value={current}
      onChange={choose}
      label={t("language")}
      disabled={saving}
    />
  )
}
