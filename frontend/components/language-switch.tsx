"use client"

import { useLocale, useTranslations } from "next-intl"
import { useSyncExternalStore } from "react"

import { MenuPill } from "@/components/menu-pill"
import { LANGUAGE_NAMES, type Locale } from "@/constants/i18n"
import { HREFLANG_CODES } from "@/constants/seo"
import { isLocale } from "@/lib/locale"

/** Calls `changed` whenever the page's head changes (each page sets its own). */
function onHeadChange(changed: () => void) {
  const observer = new MutationObserver(changed)
  observer.observe(document.head, { childList: true, subtree: true })

  return () => observer.disconnect()
}

/** The page's own language versions, as its head names them for search engines (hreflang):
 * each language and its address, as a string that stays the same while they do. */
function pageVersions() {
  const byCode = Object.fromEntries(
    Object.entries(HREFLANG_CODES).map(([locale, code]) => [code, locale])
  )

  return [
    ...document.head.querySelectorAll<HTMLLinkElement>(
      'link[rel="alternate"][hreflang]'
    ),
  ]
    .flatMap((link) => {
      const code = link.getAttribute("hreflang") ?? ""
      const locale = byCode[code] ?? code

      return isLocale(locale)
        ? [`${locale} ${new URL(link.href).pathname}`]
        : []
    })
    .join("\n")
}

/** The language menu for a page that has versions in other languages: each opens that version
 * with a plain link, as search engines see them. Nothing on a page with one address. */
export function LanguageSwitch() {
  const t = useTranslations("nav")
  const locale = useLocale()
  const versions = useSyncExternalStore(onHeadChange, pageVersions, () => "")
    .split("\n")
    .filter(Boolean)
    .map((line) => {
      const [language, path] = line.split(" ")

      return { locale: language as Locale, path }
    })

  if (versions.length < 2) {
    return null
  }

  return (
    <MenuPill
      ariaLabel={t("language")}
      value={locale}
      options={versions.map((version) => ({
        value: version.locale,
        label: LANGUAGE_NAMES[version.locale],
        keepCase: true,
        href: version.path,
      }))}
      onChange={() => {}}
      className="h-10 w-auto px-5 pe-12 text-sm [&>svg]:end-4 [&>svg]:size-5"
    />
  )
}
