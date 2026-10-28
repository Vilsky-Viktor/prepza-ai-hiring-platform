"use client"

import { cn } from "cn"
import { usePathname } from "next/navigation"
import { useTranslations } from "next-intl"

import { useAuth } from "@/providers/auth-provider"
import { LocalizedLink, useUrlLocale } from "@/components/common/localized-link"
import { NAV_LINKS } from "@/config/navigation"
import { localizeHref } from "@/lib/locale-path"

export function SiteNav() {
  const t = useTranslations("nav")
  const pathname = usePathname()
  const { user, loading } = useAuth()
  const locale = useUrlLocale()

  return (
    // The negative margin cancels the first link's padding, so the separator sits evenly.
    // globals.css finds it by data-slot to add the blue dots; the label is translated.
    <nav
      data-slot="main-nav"
      className="-ms-1.5 flex h-8 items-center sm:-ms-2.5"
      aria-label={t("main")}
    >
      {NAV_LINKS.map((link) => {
        if (link.signedInOnly && (loading || !user)) {
          return null
        }

        // Against the address in the page's language (/de/pricing).
        const href = localizeHref(locale, link.href)
        const current = link.exact
          ? pathname === href
          : pathname.startsWith(href)

        return (
          <LocalizedLink
            key={link.href}
            href={link.href}
            aria-current={current ? "page" : undefined}
            className={cn(
              "rounded-lg px-1.5 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground active:bg-surface active:text-foreground sm:px-2.5",
              current && "text-foreground"
            )}
          >
            {t(link.label)}
          </LocalizedLink>
        )
      })}
    </nav>
  )
}
