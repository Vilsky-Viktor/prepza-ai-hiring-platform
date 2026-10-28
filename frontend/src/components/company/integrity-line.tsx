import { getTranslations } from "next-intl/server"
import { cn } from "cn"
import { WARNING_TONE } from "@/constants/tones"
import { Dot } from "@/components/dot"

/** What the candidate's browser and timing showed; counts above zero stand out. */
export async function IntegrityLine({
  session,
}: {
  session: { tab_leaves: number; copies: number; fast_answers: number }
}) {
  const t = await getTranslations("candidates")
  const signals = [
    t("pageLeaves", { count: session.tab_leaves }),
    t("copies", { count: session.copies }),
    t("fastAnswers", { count: session.fast_answers }),
  ]
  const counts = [session.tab_leaves, session.copies, session.fast_answers]

  return (
    <p className="flex flex-wrap items-center gap-x-1.5 text-sm text-muted-foreground tabular-nums">
      {signals.map((signal, index) => (
        <span key={signal} className="flex items-center gap-x-1.5">
          {index > 0 && <Dot className="mx-0" />}
          <span className={cn(counts[index] > 0 && WARNING_TONE)}>
            {signal}
          </span>
        </span>
      ))}
    </p>
  )
}
