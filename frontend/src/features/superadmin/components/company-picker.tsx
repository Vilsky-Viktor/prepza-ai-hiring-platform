"use client"

import { Combobox } from "@base-ui/react/combobox"
import { cn } from "cn"
import { CheckIcon, ChevronDownIcon, SearchIcon } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"
import { useEffect, useState } from "react"

import { MAX_SEARCH_LENGTH } from "@/config/limits"
import { SEARCH_DELAY_MS } from "@/config/lists"
import { apiFetch } from "@/lib/api"
import { formatList } from "@/lib/format"
import type { CampaignCompany } from "@/types/campaigns"
import type { SuperadminCompany } from "@/types/superadmin"

/** Some companies, as the ATS link's interview picker (company/interview-picker.tsx) chooses one
 * interview: the site's select pill with a search as its menu's first row, here ticking several.
 * The chosen ones come first, then the newest companies, or those the service found by name. */
export function CompanyPicker({
  value,
  onChange,
  disabled,
}: {
  value: CampaignCompany[]
  onChange: (companies: CampaignCompany[]) => void
  disabled?: boolean
}) {
  const t = useTranslations("superadmin")
  const locale = useLocale()
  const [query, setQuery] = useState("")
  const [found, setFound] = useState<CampaignCompany[]>([])
  // The names of every company seen so far, so a chosen one keeps its name in a new search.
  const [names, setNames] = useState<Record<string, string>>(() =>
    Object.fromEntries(value.map((company) => [company.id, company.name]))
  )
  const q = query.trim()

  useEffect(() => {
    const timer = window.setTimeout(() => {
      apiFetch<SuperadminCompany[]>(
        `/companies/superadmin/companies?q=${encodeURIComponent(q)}`
      )
        .then((rows) => {
          const companies = rows.map(({ id, name }) => ({ id, name }))
          setNames((known) => ({
            ...known,
            ...Object.fromEntries(
              companies.map((item) => [item.id, item.name])
            ),
          }))
          setFound(companies)
        })
        .catch(() => {})
    }, SEARCH_DELAY_MS)

    return () => window.clearTimeout(timer)
  }, [q])

  const chosen = value.map((company) => company.id)
  const items = [
    ...chosen,
    ...found.map((item) => item.id).filter((id) => !chosen.includes(id)),
  ]
  const label = (id: string) => names[id] ?? ""

  return (
    <Combobox.Root
      multiple
      items={items}
      value={chosen}
      onValueChange={(ids: string[]) =>
        onChange(ids.map((id) => ({ id, name: label(id) })))
      }
      onInputValueChange={setQuery}
      itemToStringLabel={label}
      // The service searches; the list shows what it found.
      filter={null}
      disabled={disabled}
    >
      <Combobox.Trigger
        aria-label={t("campaignCompanies")}
        className={cn(
          "relative flex h-14 w-full items-center rounded-xl border border-transparent bg-surface px-6 pe-16 text-start text-lg transition-colors outline-none focus-visible:border-ring-gradient disabled:opacity-50",
          chosen.length === 0 && "text-placeholder"
        )}
        data-testid="campaign-companies"
      >
        <span className={cn("truncate", chosen.length > 0 && "normal-case")}>
          {chosen.length > 0
            ? formatList(chosen.map(label), locale)
            : t("campaignCompaniesPlaceholder")}
        </span>
        <ChevronDownIcon
          aria-hidden
          className="pointer-events-none absolute end-6 top-1/2 size-6 -translate-y-1/2 text-muted-foreground"
        />
      </Combobox.Trigger>
      <Combobox.Portal>
        <Combobox.Positioner sideOffset={6} align="start" className="z-50">
          <Combobox.Popup className="w-(--anchor-width) overflow-hidden rounded-xl bg-popover text-popover-foreground shadow-md ring-1 ring-foreground/10">
            <div className="flex items-center gap-3 border-b px-5 focus-within:border-ring">
              <SearchIcon className="size-5 shrink-0 text-muted-foreground" />
              <Combobox.Input
                maxLength={MAX_SEARCH_LENGTH}
                placeholder={t("campaignCompaniesSearch")}
                aria-label={t("campaignCompaniesSearch")}
                dir="auto"
                className="h-14 w-full bg-transparent text-lg outline-none placeholder:text-placeholder"
              />
            </div>
            <Combobox.Empty className="px-6 py-3 text-base text-muted-foreground empty:hidden">
              {t("campaignCompaniesNone")}
            </Combobox.Empty>
            <Combobox.List className="max-h-72 overflow-y-auto p-2">
              {(id: string) => (
                <Combobox.Item
                  key={id}
                  value={id}
                  className="flex cursor-default items-center justify-between gap-2 rounded-lg px-4 py-2.5 text-lg outline-none select-none data-highlighted:bg-surface data-highlighted:text-accent-foreground"
                >
                  <span className="normal-case">{label(id)}</span>
                  <Combobox.ItemIndicator>
                    <CheckIcon className="size-5" />
                  </Combobox.ItemIndicator>
                </Combobox.Item>
              )}
            </Combobox.List>
          </Combobox.Popup>
        </Combobox.Positioner>
      </Combobox.Portal>
    </Combobox.Root>
  )
}
