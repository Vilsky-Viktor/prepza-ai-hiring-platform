import * as Sentry from "@sentry/nextjs"
import { getRequestConfig } from "next-intl/server"
import { cookies, headers } from "next/headers"

import { DEFAULT_LOCALE, LOCALE_COOKIE } from "@/constants/i18n"
import { LOCALE_HEADER, PLAIN_ADDRESS_HEADER } from "@/constants/seo"
import { isLocale, preferredLocale } from "@/lib/locale"

// The interface language: the address's (/de/pricing, set by proxy.ts), and English on the plain
// address of a page with language versions (/pricing), whatever the visitor chose; else the
// signed-in user's setting, which auth-provider.tsx keeps in a cookie. Without either (a first
// visit), the browser's preferred language if we support it, on private pages only: proxy.ts
// leaves it out of public ones.
export default getRequestConfig(async () => {
  const requestHeaders = await headers()
  const value =
    requestHeaders.get(LOCALE_HEADER) ??
    (requestHeaders.has(PLAIN_ADDRESS_HEADER)
      ? DEFAULT_LOCALE
      : (await cookies()).get(LOCALE_COOKIE)?.value)
  const locale =
    value && isLocale(value)
      ? value
      : (preferredLocale(requestHeaders.get("accept-language")) ??
        DEFAULT_LOCALE)

  const english = (await import("../../messages/en.json")).default
  const messages =
    locale === DEFAULT_LOCALE
      ? english
      : withFallback(
          english,
          (await import(`../../messages/${locale}.json`)).default
        )

  // A message that can't be shown (a missing key, a wrong argument) is reported, never silent;
  // English text a translation lacks comes from withFallback, and `pnpm check:messages` lists it.
  return {
    locale,
    messages,
    onError: (error) => Sentry.captureException(error),
  }
})

type Messages = { [key: string]: string | string[] | Messages }

/** The translation, with English for any text it doesn't have yet: new text is written in English
 *  first and translated later (`pnpm check:messages` lists what's missing). */
function withFallback(english: Messages, translated: Messages): Messages {
  const merged: Messages = { ...english }

  for (const [key, value] of Object.entries(translated)) {
    const base = english[key]

    merged[key] =
      value &&
      typeof value === "object" &&
      !Array.isArray(value) &&
      base &&
      typeof base === "object" &&
      !Array.isArray(base)
        ? withFallback(base, value)
        : value
  }

  return merged
}
