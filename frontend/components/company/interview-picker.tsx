"use client"

import { Combobox } from "@base-ui/react/combobox"
import { cn } from "cn"
import { CheckIcon, ChevronDownIcon, SearchIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useEffect, useState } from "react"

import { MAX_SEARCH_LENGTH } from "@/constants/limits"
import { SEARCH_DELAY_MS } from "@/constants/lists"
import { apiFetch } from "@/lib/api"
import type { Interview } from "@/types/company"

type Choice = { value: string; label: string; keepCase?: boolean }

/** The ATS link's interview, as the site's select pill (menu-pill.tsx), with a search field:
 * the newest interviews first, and any of the company's interviews by its title, found by the
 * service. `first` is a choice above them (a new interview from the job). */
export function InterviewPicker({
  companyId,
  interviews,
  first,
  value,
  onChange,
  ariaLabel,
  placeholder,
  disabled,
}: {
  companyId: string
  interviews: Interview[]
  first: Choice
  value: string | null
  onChange: (value: string) => void
  ariaLabel: string
  placeholder: string
  disabled?: boolean
}) {
  const t = useTranslations("ats")
  const [query, setQuery] = useState("")
  // What the service found for the query, and the titles of every interview seen so far, so
  // the chosen one keeps its name in a new search.
  const [found, setFound] = useState<{ q: string; rows: Interview[] }>({
    q: "",
    rows: [],
  })
  const [titles, setTitles] = useState<Record<string, string>>(() =>
    Object.fromEntries(interviews.map((item) => [item.id, item.title ?? ""]))
  )
  const q = query.trim()
  const label = (id: string) =>
    id === first.value ? first.label : (titles[id] ?? "")
  // Something typed in the menu's search.
  const typed = q !== ""

  useEffect(() => {
    if (!typed) {
      return
    }

    const timer = window.setTimeout(() => {
      apiFetch<Interview[]>(
        `/companies/interviews?company_id=${companyId}&limit=100&q=${encodeURIComponent(q)}`
      )
        .then((rows) => {
          const ready = rows.filter((item) => item.set_id)
          setTitles((known) => ({
            ...known,
            ...Object.fromEntries(
              ready.map((item) => [item.id, item.title ?? ""])
            ),
          }))
          setFound({ q, rows: ready })
        })
        .catch(() => {})
    }, SEARCH_DELAY_MS)

    return () => window.clearTimeout(timer)
  }, [typed, q, companyId])

  const shown = typed ? found.rows : interviews
  // The search came back empty: said under the first choice, which is always there.
  const nothing = typed && found.q === q && found.rows.length === 0
  const choices = [first.value, ...shown.map((item) => item.id)]

  return (
    <Combobox.Root
      items={choices}
      value={value}
      onValueChange={(next: string | null) => next && onChange(next)}
      onInputValueChange={setQuery}
      itemToStringLabel={label}
      // The service searches; the list shows what it found.
      filter={null}
      disabled={disabled}
    >
      <Combobox.Trigger
        aria-label={ariaLabel}
        className={cn(
          "relative flex h-14 w-full items-center rounded-full border border-transparent bg-muted px-6 pe-16 text-start text-lg transition-colors outline-none focus-visible:border-ring disabled:opacity-50 dark:bg-input/30",
          !value && "text-muted-foreground"
        )}
      >
        <span
          className={cn("truncate", value !== first.value && "normal-case")}
        >
          {value ? label(value) : placeholder}
        </span>
        <ChevronDownIcon
          aria-hidden
          className="pointer-events-none absolute end-6 top-1/2 size-6 -translate-y-1/2 text-muted-foreground"
        />
      </Combobox.Trigger>
      <Combobox.Portal>
        <Combobox.Positioner sideOffset={6} align="start" className="z-50">
          <Combobox.Popup className="w-(--anchor-width) overflow-hidden rounded-xl bg-popover text-popover-foreground shadow-md ring-1 ring-foreground/10">
            {/* The search as the menu's first row, like the language picker's in Settings. */}
            <div className="flex items-center gap-3 border-b px-5 focus-within:border-ring">
              <SearchIcon className="size-5 shrink-0 text-muted-foreground" />
              <Combobox.Input
                maxLength={MAX_SEARCH_LENGTH}
                placeholder={t("searchInterview")}
                aria-label={t("searchInterview")}
                dir="auto"
                className="h-14 w-full bg-transparent text-lg outline-none placeholder:text-muted-foreground"
              />
            </div>
            <Combobox.List className="max-h-72 overflow-y-auto p-2">
              {(id: string) => (
                <Combobox.Item
                  key={id}
                  value={id}
                  className="flex cursor-default items-center justify-between gap-2 rounded-lg px-4 py-2.5 text-lg outline-none select-none data-highlighted:bg-accent data-highlighted:text-accent-foreground"
                >
                  <span
                    className={id === first.value ? "lowercase" : "normal-case"}
                  >
                    {label(id)}
                  </span>
                  <Combobox.ItemIndicator>
                    <CheckIcon className="size-5" />
                  </Combobox.ItemIndicator>
                </Combobox.Item>
              )}
            </Combobox.List>
            {nothing && (
              <p className="border-t px-6 py-3 text-base text-muted-foreground">
                {t("noInterview")}
              </p>
            )}
          </Combobox.Popup>
        </Combobox.Positioner>
      </Combobox.Portal>
    </Combobox.Root>
  )
}
