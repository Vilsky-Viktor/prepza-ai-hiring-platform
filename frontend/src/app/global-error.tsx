"use client"

import { NextIntlClientProvider } from "next-intl"
import { useEffect, useState } from "react"

import { cn } from "cn"

import ErrorPage from "@/app/error"
import { FONT_VARIABLES } from "@/constants/fonts"
import { DEFAULT_LOCALE, LOCALE_COOKIE, type Locale } from "@/constants/i18n"
import { isLocale, preferredLocale, textDirection } from "@/lib/locale"

import "./globals.css"

type Messages = Record<string, unknown>

/** The visitor's language: their chosen one (the cookie), else the browser's. */
function visitorLocale() {
  const chosen = document.cookie
    .split("; ")
    .find((part) => part.startsWith(`${LOCALE_COOKIE}=`))
    ?.split("=")[1]

  return chosen && isLocale(chosen)
    ? chosen
    : (preferredLocale(navigator.languages.join(",")) ?? DEFAULT_LOCALE)
}

/** When the root layout itself failed, Next.js shows this instead of the whole document: the
 * same error page, in the visitor's language, loaded only now (the layout's messages are gone
 * with it), with the app's styles. */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const [found, setFound] = useState<{ locale: Locale; messages: Messages }>()

  useEffect(() => {
    const locale = visitorLocale()

    import(`../../messages/${locale}.json`)
      .catch(() => import("../../messages/en.json"))
      .then((loaded) => setFound({ locale, messages: loaded.default }))
  }, [])

  return (
    <html
      lang={found?.locale ?? DEFAULT_LOCALE}
      dir={textDirection(found?.locale ?? DEFAULT_LOCALE)}
      className={cn("antialiased", ...FONT_VARIABLES, "font-sans")}
    >
      <body className="flex min-h-svh flex-col">
        {found && (
          <NextIntlClientProvider
            locale={found.locale}
            messages={found.messages}
          >
            <ErrorPage error={error} reset={reset} />
          </NextIntlClientProvider>
        )}
      </body>
    </html>
  )
}
