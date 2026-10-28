"use client"

import { CopyIcon, LogOutIcon, ZapIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { IconStat } from "@/components/icon-stat"
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
    <IconStat
      key={label}
      label={label}
      icon={<Icon aria-hidden className="size-4" />}
      className="gap-1 text-amber-700 hover:text-amber-700 dark:text-amber-400 dark:hover:text-amber-400"
    >
      {count}
    </IconStat>
  ))
}
