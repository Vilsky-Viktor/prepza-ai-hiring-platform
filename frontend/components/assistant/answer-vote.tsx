"use client"

import { cn } from "cn"
import { ThumbsDownIcon, ThumbsUpIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { Button } from "@/components/ui/button"
import { FEEDBACK_HOVER_CLASS } from "@/constants/feedback"
import type { Vote } from "@/types/assistant"

/** Small thumbs up and down under one of the assistant's answers, on its right, as candidates rate a question
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
    <div className="flex justify-end gap-0.5" data-testid="answer-vote">
      {thumbs.map(({ vote, label, Icon }) => (
        <Button
          key={vote}
          type="button"
          variant="ghost"
          size="icon-sm"
          aria-label={label}
          aria-pressed={value === vote}
          className={FEEDBACK_HOVER_CLASS}
          onClick={() => onVote(value === vote ? null : vote)}
        >
          <Icon
            className={cn(
              "size-4",
              value === vote && "fill-primary text-primary"
            )}
          />
        </Button>
      ))}
    </div>
  )
}
