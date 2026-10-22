"use client"

import { useTranslations } from "next-intl"

import { Dotted } from "@/components/dot"
import type { ReviewItem } from "@/types/round"

/** A multi-answer answer's points: the right options picked of all, any wrong ones, and the
 * points earned, as the backend scored them ("2 of 3 right options · 0.67 of 1 point"). Nothing
 * for a single-answer question, or one unanswered or timed out. */
export function AnswerPoints({ item }: { item: ReviewItem }) {
  const t = useTranslations("rounds")
  const answer = item.answer

  if (!item.multi || !answer || answer.timed_out || answer.score == null) {
    return null
  }

  return (
    <p
      data-testid="answer-points"
      className="text-sm text-muted-foreground tabular-nums"
    >
      <Dotted
        items={[
          t("rightPicks", {
            right: answer.right_picks ?? 0,
            total: item.correct_indexes?.length ?? 0,
          }),
          (answer.wrong_picks ?? 0) > 0 &&
            t("wrongPicks", { count: answer.wrong_picks ?? 0 }),
          t("points", { points: answer.score / 100 }),
        ]}
      />
    </p>
  )
}
