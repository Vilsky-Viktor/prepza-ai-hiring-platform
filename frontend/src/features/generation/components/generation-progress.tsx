"use client"

import { useTranslations } from "next-intl"
import type { ReactNode } from "react"

import { AiPulse } from "@/components/common/ai-pulse"
import { BackLink } from "@/components/common/back-link"
import { WritingProgress } from "@/components/common/writing-progress"
import type { Generation } from "@/types/generation"

export function GenerationProgress({
  generation,
  backHref,
  backLabel,
  action,
}: {
  generation: Generation
  backHref: string
  backLabel: string
  action?: ReactNode
}) {
  const t = useTranslations("generation")
  const progress = generation.progress
  const writing = progress !== null && progress.total > 0

  return (
    <div className="flex flex-1 flex-col items-center justify-center space-y-8 text-center">
      <AiPulse className="size-20" />
      <div className="space-y-4">
        <div className="relative">
          <BackLink href={backHref} help="generating">
            {backLabel}
          </BackLink>
          <h1 className="font-heading text-4xl font-medium tracking-tight text-balance sm:text-5xl">
            {writing ? t("writing") : t("drafting")}
          </h1>
        </div>
        <p className="text-base text-muted-foreground">
          {writing ? t("writingNote") : t("draftingNote")}
        </p>
      </div>
      {writing && <WritingProgress progress={progress} />}
      {action && <div className="flex justify-center pt-6">{action}</div>}
    </div>
  )
}
