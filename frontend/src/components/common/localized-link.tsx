"use client"

import Link from "next/link"
import { createContext, useContext, type ComponentProps } from "react"

import { localizeHref } from "@/lib/locale-path"

// The language of the address the page was asked for (/de/pricing: de), set by the root layout
// from proxy.ts's header; null for a plain address.
const UrlLocale = createContext<string | null>(null)

export function UrlLocaleProvider({
  locale,
  children,
}: {
  locale: string | null
  children: React.ReactNode
}) {
  return <UrlLocale value={locale}>{children}</UrlLocale>
}

/** The language of the page's address, or null for a plain address. */
export function useUrlLocale() {
  return useContext(UrlLocale)
}

/** A link that stays in the language of the address it's on: from /de/pricing, "/faq" leads to
 * /de/faq; other targets, and every link on a plain address, are left as they are. */
export function LocalizedLink({
  href,
  ...props
}: ComponentProps<typeof Link> & { href: string }) {
  const locale = useUrlLocale()

  return <Link href={localizeHref(locale, href)} {...props} />
}
