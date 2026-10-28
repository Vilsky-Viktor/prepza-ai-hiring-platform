"use client"

import { cn } from "cn"
import { ThumbsDownIcon, ThumbsUpIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { Button } from "@/components/ui/button"
import { FEEDBACK_HOVER_CLASS } from "@/config/feedback"
import type { Vote } from "@/types/assistant"

/** Small thumbs up and down in a little card on the bottom edge of one of the assistant's
 * answers, at its end, as candidates rate a question
 * (QuestionRating): the vote given is filled. Clicking it again clears it; the other one
 * changes it. */
export function AnswerVote({
  value,
  onVote,
}: {
  value: Vote | null
  onVote: (value: Vote | null) => void
}) {
  const t = useTranslations("assistant")
  const thumbs = [
    { vote: 1 as const, label: t("goodAnswer"), Icon: ThumbsUpIcon },
    { vote: -1 as const, label: t("badAnswer"), Icon: ThumbsDownIcon },
  ]

  return (
    <div
      className="flex items-center gap-0.5 rounded-xl border bg-popover px-1"
      data-testid="answer-vote"
    >
      {thumbs.map(({ vote, label, Icon }) => (
        <Button
          key={vote}
          type="button"
          variant="ghost"
          size="icon-xs"
          aria-label={label}
          aria-pressed={value === vote}
          className={FEEDBACK_HOVER_CLASS}
          onClick={() => onVote(value === vote ? null : vote)}
        >
          <Icon
            className={cn(
              "size-3.5",
              value === vote && "fill-primary text-primary"
            )}
          />
        </Button>
      ))}
    </div>
  )
}
