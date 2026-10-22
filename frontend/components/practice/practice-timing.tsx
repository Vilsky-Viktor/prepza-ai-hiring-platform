"use client"

import { ChevronDownIcon, TimerIcon } from "lucide-react"
import { useLocale, useTranslations } from "next-intl"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { formatSeconds } from "@/lib/format"
import type { PracticeTiming as Timing, PracticeTimingId } from "@/types/round"

/** The time per question of a practice round, chosen among the options the API sends before
 * it starts: the standard time, more, or no time limit. Looks like the invites' extra time. */
export function PracticeTiming({
  timings,
  value,
  onChange,
  disabled,
}: {
  timings: Timing[]
  value: PracticeTimingId
  onChange: (value: PracticeTimingId) => void
  disabled?: boolean
}) {
  const t = useTranslations("practice")
  const locale = useLocale()
  const label = (seconds: number | null) =>
    seconds === null
      ? t("timingNone")
      : t("timingPerQuestion", { time: formatSeconds(seconds, locale) })
  const current = timings.find((timing) => timing.id === value)

  if (!current) {
    return null
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            variant="outline"
            className="h-12 gap-1.5 px-4 text-base"
            disabled={disabled}
            data-testid="practice-timing"
          />
        }
      >
        <TimerIcon aria-hidden />
        {label(current.seconds)}
        <ChevronDownIcon className="text-muted-foreground" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56 p-2">
        <p className="px-3 py-2 text-xs text-muted-foreground">
          {t("timingNote")}
        </p>
        <DropdownMenuRadioGroup
          value={value}
          onValueChange={(id) => onChange(id as PracticeTimingId)}
        >
          {timings.map((timing) => (
            <DropdownMenuRadioItem
              key={timing.id}
              value={timing.id}
              className="px-3 py-2 lowercase"
            >
              {label(timing.seconds)}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
