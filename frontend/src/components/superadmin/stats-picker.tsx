"use client"

import { ChevronDownIcon } from "lucide-react"
import { useFormatter, useTranslations } from "next-intl"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { statsMonths, statsYears, type StatsChoice } from "@/lib/stats-period"

const ITEM = "px-3 py-2"

/** "All time" as a checkbox, and the period in the site's menu, like the pass rates' sort: a
 * grey pill opening one choice in two columns, a month with its year (a monthly report) or a
 * year (an annual report). The menu is off while all time is on and keeps its period for when
 * it's off again. */
export function StatsPicker({
  choice,
  onChange,
}: {
  choice: StatsChoice
  onChange: (choice: StatsChoice) => void
}) {
  const t = useTranslations("superadmin")
  const format = useFormatter()
  const now = new Date()
  // A year names itself; a month is shown with its year.
  const label = (period: string) =>
    period.length === 4
      ? period
      : format.dateTime(new Date(`${period}-15T12:00:00Z`), {
          month: "long",
          year: "numeric",
          timeZone: "UTC",
        })

  return (
    <div className="flex flex-wrap items-center justify-end gap-6">
      <label className="flex cursor-pointer items-center gap-3 text-base">
        <Checkbox
          className="size-6 shrink-0 [&_[data-slot=checkbox-indicator]>svg]:size-4"
          checked={choice.allTime}
          onCheckedChange={(checked) =>
            onChange({ ...choice, allTime: checked === true })
          }
        />
        {t("statsAllTime")}
      </label>
      <DropdownMenu>
        {/* Looks like the site's select (components/pill-select.tsx); opens the site's menu. */}
        <DropdownMenuTrigger
          disabled={choice.allTime}
          render={
            <Button
              type="button"
              variant="ghost"
              aria-label={t("statsPeriod")}
              className="relative h-14 w-60 justify-start rounded-xl bg-surface px-6 pe-16 text-lg font-normal normal-case hover:bg-surface"
            />
          }
        >
          {label(choice.period)}
          <ChevronDownIcon
            aria-hidden
            className="pointer-events-none absolute end-6 top-1/2 size-6 -translate-y-1/2 text-muted-foreground"
          />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-80 p-2">
          <DropdownMenuRadioGroup
            value={choice.period}
            onValueChange={(period) => onChange({ ...choice, period })}
            className="grid grid-cols-2 gap-2"
          >
            <div>
              {statsMonths(now).map((period) => (
                <DropdownMenuRadioItem
                  key={period}
                  value={period}
                  className={ITEM}
                >
                  {label(period)}
                </DropdownMenuRadioItem>
              ))}
            </div>
            <div className="border-s ps-2">
              {statsYears(now).map((period) => (
                <DropdownMenuRadioItem
                  key={period}
                  value={period}
                  className={ITEM}
                >
                  {period}
                </DropdownMenuRadioItem>
              ))}
            </div>
          </DropdownMenuRadioGroup>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
