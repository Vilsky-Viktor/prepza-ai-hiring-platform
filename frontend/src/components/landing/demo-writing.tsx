import { cn } from "cn"
import { CheckIcon, LoaderCircleIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { AiPulse } from "@/components/ai-pulse"
import { Progress } from "@/components/ui/progress"

/** The questions being written, as the generation page shows it (components/generation/
 * generation-progress.tsx), small: its loading mark and title, the bar with its percent and the
 * topics `ready`, and each topic checked off once its questions are written. The percent is the
 * share of topics ready, so the two always agree. */
export function DemoWriting({
  topics,
  ready,
}: {
  topics: string[]
  ready: number
}) {
  const t = useTranslations("generation")
  const percent = Math.round((ready / topics.length) * 100)

  return (
    <div className="flex flex-1 flex-col justify-center gap-4 px-2">
      <div className="flex items-center gap-3">
        <AiPulse className="size-8" />
        <p className="font-heading text-base font-medium">{t("writing")}</p>
      </div>
      <div className="space-y-1">
        <Progress value={percent} />
        <p className="flex justify-between text-xs text-muted-foreground tabular-nums">
          <span>{t("topicsReady", { ready, count: topics.length })}</span>
          <span>{percent}%</span>
        </p>
      </div>
      <ul className="space-y-2">
        {topics.map((topic, position) => (
          <li key={topic} className="flex items-center gap-3">
            {position < ready ? (
              <CheckIcon className="size-4 shrink-0 text-primary" />
            ) : (
              <LoaderCircleIcon className="size-4 shrink-0 animate-spin text-muted-foreground" />
            )}
            <span
              className={cn(
                "truncate",
                position >= ready && "text-muted-foreground"
              )}
            >
              {topic}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
