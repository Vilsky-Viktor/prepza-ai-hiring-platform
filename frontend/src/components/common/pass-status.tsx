import { cn } from "cn"
import { useTranslations } from "next-intl"

import { gradeTone } from "@/lib/grade-tone"
import { Dot } from "@/components/common/dot"

/** Whether a candidate passed, in the grade's green or red, then the test's passing grade, muted
 * (it's about the test, not the candidate); "not finished yet" while undecided. */
export function PassStatus({
  passed,
  passMark,
}: {
  passed: boolean | null
  passMark: number
}) {
  const t = useTranslations("report")

  if (passed == null) {
    return <span className="text-muted-foreground">{t("notFinished")}</span>
  }

  return (
    <span className="text-muted-foreground">
      <span className={cn(gradeTone(passed))}>
        {t(passed ? "statusPassed" : "statusNotPassed")}
      </span>
      <Dot />
      {t("passMark", { mark: passMark })}
    </span>
  )
}
