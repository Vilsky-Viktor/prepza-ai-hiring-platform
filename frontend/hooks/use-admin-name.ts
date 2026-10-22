import { useTranslations } from "next-intl"

import { hasMessage } from "@/lib/messages"

// The admin zone's groups naming the values the API sends.
type Group =
  | "limitNames"
  | "limitWindows"
  | "limitKinds"
  | "limitScopes"
  | "limitServices"
  | "aiCategories"
  | "aiActions"
  | "legalDocuments"
  | "flags"
  | "kinds"

/** A value from the API by its name in one of the admin zone's groups (a limit, its window, an
 * AI action, a flag…), or as it is when the group has none. */
export function useAdminName() {
  const t = useTranslations("superadmin")

  return (group: Group, value: string | number) => {
    const key = `${group}.${value}` as const

    return hasMessage(t, key) ? t(key) : String(value)
  }
}
