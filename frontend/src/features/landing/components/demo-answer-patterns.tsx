"use client"

import { TriangleAlertIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { CornerSign } from "@/components/common/corner-sign"
import { SIGN_CARD } from "@/config/cards"
import type { DemoCandidate } from "@/config/reports-demo"

/** What a candidate's answers and times show (features/company/components/answer-patterns.tsx),
 * for the landing: the signals that fired under the amber sign, the note that they aren't proof,
 * and a question they got right to ask about in a live interview. */
export function DemoAnswerPatterns({
  patterns,
}: {
  patterns: NonNullable<DemoCandidate["patterns"]>
}) {
  const t = useTranslations("answerPatterns")
  const { followUp } = patterns

  return (
    <section className={`${SIGN_CARD} space-y-5`}>
      <CornerSign>
        <TriangleAlertIcon className="text-amber-600 dark:text-amber-400" />
      </CornerSign>
      <div className="space-y-2 text-base">
        <p className="font-medium">{t("title")}</p>
        <ul className="space-y-1">
          {patterns.timing && <li>{t("timing")}</li>}
          {patterns.personFit && <li>{t("personFit", patterns.personFit)}</li>}
        </ul>
        <p className="text-sm text-muted-foreground">{t("note")}</p>
      </div>
      <div className="space-y-3">
        <p className="text-sm font-medium">{t("askTitle")}</p>
        <div className="space-y-1.5">
          <p className="text-sm text-muted-foreground">{followUp.topic}</p>
          <p className="font-light">{followUp.text}</p>
          <p className="text-sm">
            {t.rich("ask", {
              answer: followUp.right,
              other: followUp.wrong,
              b: (chunks) => <bdi className="font-medium">{chunks}</bdi>,
            })}
          </p>
        </div>
      </div>
    </section>
  )
}
