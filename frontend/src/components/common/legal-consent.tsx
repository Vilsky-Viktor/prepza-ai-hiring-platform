"use client"

import Link from "next/link"
import { useTranslations } from "next-intl"

/** Shown wherever someone signs in: signing in accepts the terms. */
export function LegalConsent() {
  const t = useTranslations("signIn")

  return (
    <p className="text-center text-sm text-balance text-muted-foreground">
      {/* Two even lines, in any language. */}
      {t.rich("consent", {
        terms: (chunks) => (
          <Link href="/terms" className="underline underline-offset-4">
            {chunks}
          </Link>
        ),
        privacy: (chunks) => (
          <Link href="/privacy" className="underline underline-offset-4">
            {chunks}
          </Link>
        ),
      })}
    </p>
  )
}
