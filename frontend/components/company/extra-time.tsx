"use client"

import { ChevronDownIcon, TimerIcon } from "lucide-react"
import { useRouter } from "next/navigation"
import { useLocale, useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { formatPercent } from "@/lib/format"

/** Extra time on each question for a candidate who needs it (an accommodation), chosen among
 * the amounts the API offers before the candidate starts; shown as set afterwards. */
export function ExtraTime({
  interviewId,
  inviteId,
  current,
  options,
}: {
  interviewId: string
  inviteId: string
  current: number
  options: number[]
}) {
  const t = useTranslations("candidates")
  const locale = useLocale()
  const router = useRouter()
  const [busy, setBusy] = useState(false)
  const label = (percent: number) =>
    percent
      ? t("extraTimeSome", { percent: formatPercent(percent, locale) })
      : t("extraTimeNone")

  async function choose(value: string) {
    setBusy(true)

    try {
      await apiFetch(
        `/companies/interviews/${interviewId}/candidates/${inviteId}/extra-time`,
        { method: "PUT", body: JSON.stringify({ extra_time: Number(value) }) }
      )
      router.refresh()
    } catch (error) {
      toast.error(apiErrorMessage(error, t("extraTimeFailed")))
    } finally {
      setBusy(false)
    }
  }

  // Started: the time is fixed, so it only shows when some was given.
  if (options.length === 0) {
    return current ? (
      <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
        <TimerIcon aria-hidden className="size-4" />
        {label(current)}
      </span>
    ) : null
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button variant="outline" className="gap-1.5" disabled={busy} />
        }
      >
        <TimerIcon aria-hidden />
        {label(current)}
        <ChevronDownIcon className="text-muted-foreground" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56 p-2">
        <p className="px-3 py-2 text-xs text-muted-foreground">
          {t("extraTimeNote")}
        </p>
        <DropdownMenuRadioGroup value={String(current)} onValueChange={choose}>
          {options.map((percent) => (
            <DropdownMenuRadioItem
              key={percent}
              value={String(percent)}
              className="px-3 py-2 lowercase"
            >
              {label(percent)}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
