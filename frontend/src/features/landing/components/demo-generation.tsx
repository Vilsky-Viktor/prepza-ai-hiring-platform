"use client"

import { useTranslations } from "next-intl"

import { AiPulse } from "@/components/common/ai-pulse"
import { WritingProgress } from "@/components/common/writing-progress"

/** The questions being written, as the generation page shows it (features/generation/
 * components/generation-progress.tsx) at its own size: prepza's loading mark, the page's title
 * and note, and the real progress, `ready` of `topics` topics done, `questions` a topic. */
export function DemoGeneration({
  topics,
  ready,
  questions,
}: {
  topics: number
  ready: number
  questions: number
}) {
  const t = useTranslations("generation")

  return (
    <div className="flex flex-1 flex-col items-center justify-center space-y-8 px-4 text-center">
      <AiPulse className="size-20" />
      <div className="space-y-4">
        <p className="font-heading text-4xl font-medium tracking-tight text-balance sm:text-5xl">
          {t("writing")}
        </p>
        <p className="text-base text-muted-foreground">{t("writingNote")}</p>
      </div>
      <WritingProgress
        progress={{
          done: ready * questions,
          total: topics * questions,
          topics,
          topics_ready: ready,
        }}
      />
    </div>
  )
}
