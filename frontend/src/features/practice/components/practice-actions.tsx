"use client"

import { HistoryIcon } from "lucide-react"
import Link from "next/link"
import { useTranslations } from "next-intl"

import { useAuth } from "@/providers/auth-provider"
import { StartPractice } from "@/features/practice/components/start-practice"
import { Button } from "@/components/ui/button"
import type { PracticeTiming } from "@/types/round"

/** A practice test's actions beside its title: the talent's past rounds (signed in), and
 * starting a new round with the time per question they choose. */
export function PracticeActions({
  templateId,
  startLabel,
  timings,
}: {
  templateId: string
  startLabel: string
  timings: PracticeTiming[]
}) {
  const t = useTranslations("practice")
  const { user } = useAuth()

  return (
    <div className="flex shrink-0 items-center gap-3">
      {user && (
        <Button
          variant="ghost"
          size="icon"
          className="size-12 shrink-0 text-muted-foreground hover:text-foreground"
          aria-label={t("history")}
          render={<Link href={`/practice/history/${templateId}`} />}
          nativeButton={false}
        >
          <HistoryIcon className="size-6" />
        </Button>
      )}
      <StartPractice
        templateId={templateId}
        label={startLabel}
        timings={timings}
      />
    </div>
  )
}
