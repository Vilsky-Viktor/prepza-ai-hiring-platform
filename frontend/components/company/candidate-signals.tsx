"use client"

import { CopyIcon, LogOutIcon, ZapIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import type { Candidate } from "@/types/company"

/** A candidate's integrity signals at a glance: page leaves, copy attempts and answers picked
 * too fast, each with its count; only the ones that happened show. */
export function CandidateSignals({
  candidate,
}: {
  candidate: Pick<Candidate, "tab_leaves" | "copies" | "fast_answers">
}) {
  const t = useTranslations("candidates")
  const signals = [
    {
      icon: LogOutIcon,
      count: candidate.tab_leaves,
      label: t("pageLeaves", { count: candidate.tab_leaves }),
    },
    {
      icon: CopyIcon,
      count: candidate.copies,
      label: t("copies", { count: candidate.copies }),
    },
    {
      icon: ZapIcon,
      count: candidate.fast_answers,
      label: t("fastAnswers", { count: candidate.fast_answers }),
    },
  ].filter((signal) => signal.count > 0)

  return signals.map(({ icon: Icon, count, label }) => (
    <Tooltip key={label}>
      <TooltipTrigger
        render={
          <span
            aria-label={label}
            className="flex items-center gap-1 text-amber-700 tabular-nums dark:text-amber-400"
          />
        }
      >
        <Icon aria-hidden className="size-4" />
        {count}
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  ))
}
