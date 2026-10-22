"use client"

import { cn } from "cn"
import { ChevronDownIcon } from "lucide-react"
import { useRouter } from "next/navigation"
import { useLocale, useTranslations } from "next-intl"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { LANGUAGE_NAMES, type Locale } from "@/constants/i18n"
import { formatList } from "@/lib/format"
import { isLocale, languageOf } from "@/lib/locale"
import { hasMessage } from "@/lib/messages"
import type { TemplateFilters } from "@/types/superadmin"

// "Any level" in the level menu; levels themselves come from the API.
const ANY = "any"
// "All languages" in the address, so a list that starts in the visitor's languages can show
// every language once that's chosen.
export const ALL_LANGUAGES = "all"
const TRIGGER = "h-10 gap-1.5 px-3 text-sm"

export type TemplateChoice = {
  q: string
  level: string | null
  // None means every language.
  languages: string[]
}

/** The address of the template list at `base` with these choices; the server renders it
 * filtered. */
function templatesHref(base: string, { q, level, languages }: TemplateChoice) {
  const params = new URLSearchParams()

  if (q) {
    params.set("q", q)
  }

  if (level) {
    params.set("level", level)
  }

  if (languages.length === 0) {
    params.set("lang", ALL_LANGUAGES)
  }

  languages.forEach((language) => params.append("lang", language))

  return `${base}?${params}`
}

function languageName(code: string) {
  return isLocale(code) ? LANGUAGE_NAMES[code as Locale] : code
}

/** A template list's level and languages, as the old public library had them. */
export function TemplateFilterBar({
  base,
  filters,
  current,
}: {
  base: string
  filters: TemplateFilters
  current: TemplateChoice
}) {
  const t = useTranslations("templates")
  const locale = useLocale()
  const router = useRouter()

  function choose(change: Partial<TemplateChoice>) {
    router.replace(templatesHref(base, { ...current, ...change }), {
      scroll: false,
    })
  }

  // A level from the API or the address, or as it is when there's no name for it.
  function levelName(level: string) {
    const key = `levels.${level}` as const

    return hasMessage(t, key) ? t(key) : level
  }

  function toggle(language: string, checked: boolean) {
    const languages = checked
      ? [...current.languages, language]
      : current.languages.filter((item) => item !== language)
    // In the API's order, so the address is the same whichever was ticked first.
    choose({
      languages: filters.languages.filter((item) => languages.includes(item)),
    })
  }

  const languagesLabel =
    current.languages.length === 0
      ? t("allLanguages")
      : current.languages.length <= 2
        ? formatList(current.languages.map(languageName), locale)
        : t("languages", { count: current.languages.length })

  return (
    <div className="flex shrink-0 items-center gap-1">
      <DropdownMenu>
        <DropdownMenuTrigger
          render={<Button type="button" variant="ghost" className={TRIGGER} />}
        >
          {t("level", {
            level: current.level ? levelName(current.level) : t("anyLevel"),
          })}
          <ChevronDownIcon className="text-muted-foreground" />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-48 p-2">
          <DropdownMenuRadioGroup
            value={current.level ?? ANY}
            onValueChange={(level) =>
              choose({ level: level === ANY ? null : level })
            }
          >
            <DropdownMenuRadioItem value={ANY} className="px-3 py-2 lowercase">
              {t("anyLevel")}
            </DropdownMenuRadioItem>
            {filters.levels.map((level) => (
              <DropdownMenuRadioItem
                key={level}
                value={level}
                className="px-3 py-2 lowercase"
              >
                {levelName(level)}
              </DropdownMenuRadioItem>
            ))}
          </DropdownMenuRadioGroup>
        </DropdownMenuContent>
      </DropdownMenu>

      <DropdownMenu>
        <DropdownMenuTrigger
          render={
            <Button
              type="button"
              variant="ghost"
              // Language names keep their capitals; "all languages" is lowercase like the rest.
              className={cn(
                TRIGGER,
                current.languages.length > 0 &&
                  current.languages.length <= 2 &&
                  "normal-case"
              )}
            />
          }
        >
          {languagesLabel}
          <ChevronDownIcon className="text-muted-foreground" />
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="start"
          className="max-h-80 w-56 overflow-y-auto p-2"
        >
          <DropdownMenuCheckboxItem
            checked={current.languages.length === 0}
            onCheckedChange={() => choose({ languages: [] })}
            className="px-3 py-2 lowercase"
          >
            {t("allLanguages")}
          </DropdownMenuCheckboxItem>
          {filters.languages.map((language) => (
            <DropdownMenuCheckboxItem
              key={language}
              {...languageOf(language)}
              checked={current.languages.includes(language)}
              onCheckedChange={(next) => toggle(language, next)}
              className="px-3 py-2"
            >
              {languageName(language)}
            </DropdownMenuCheckboxItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
