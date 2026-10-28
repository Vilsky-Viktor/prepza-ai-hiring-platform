"use client"

import { ChevronDownIcon, LanguagesIcon } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"
import { useId, useSyncExternalStore } from "react"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import type { Locale } from "@/config/i18n"
import { HREFLANG_CODES } from "@/config/seo"
import { englishLanguageName } from "@/lib/english-language-name"
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

/** The footer's language menu for a page that has versions in other languages: the page's
 * language with a languages icon, opening the list. Each opens that version with a plain link,
 * as search engines see them. Names are in English, sorted, so a visitor who can't read the
 * page's language still finds theirs. Nothing on a page with one address. */
export function LanguageSwitch() {
  const t = useTranslations("nav")
  const locale = useLocale()
  // Named by its label and the language it shows, so the visible text is in its name.
  const labelId = useId()
  const valueId = useId()
  const versions = useSyncExternalStore(onHeadChange, pageVersions, () => "")
    .split("\n")
    .filter(Boolean)
    .map((line) => {
      const [language, path] = line.split(" ")

      return {
        locale: language as Locale,
        path,
        name: englishLanguageName(language),
      }
    })
    .sort((a, b) => a.name.localeCompare(b.name, "en"))

  if (versions.length < 2) {
    return null
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        aria-labelledby={`${labelId} ${valueId}`}
        className="flex items-center gap-1.5 rounded-xl bg-surface px-2.5 py-1 leading-5 transition-colors outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring active:text-foreground"
      >
        <span id={labelId} className="sr-only">
          {t("language")}
        </span>
        <LanguagesIcon aria-hidden className="size-4" />
        <span id={valueId} lang="en" dir="ltr">
          {englishLanguageName(locale)}
        </span>
        <ChevronDownIcon aria-hidden className="size-3.5" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="max-h-80 w-56 p-2">
        <DropdownMenuRadioGroup value={locale}>
          {versions.map((version) => (
            <DropdownMenuRadioItem
              key={version.locale}
              value={version.locale}
              render={<a href={version.path} hrefLang={version.locale} />}
              className="px-3 py-2"
            >
              <span lang="en" dir="ltr">
                {version.name}
              </span>
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
