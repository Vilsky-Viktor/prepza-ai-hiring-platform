"use client"

import { cn } from "cn"
import { CheckIcon, XIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { gradeTone } from "@/lib/grade-tone"
import { InlineText } from "@/components/common/inline-text"

/** A question's answer options: the right ones with a green check, the wrong ones with a red
 * cross, in the scorecards' colors. `picked` marks the options a talent or candidate chose. */
export function AnswerOptions({
  options,
  picked,
  className,
}: {
  options: { answer: string; correct: boolean }[]
  picked?: number[]
  className?: string
}) {
  const t = useTranslations("questions")

  return (
    <ul className={cn("space-y-1.5 text-sm", className)}>
      {options.map((option, index) => (
        <li
          key={index}
          className={cn(
            "flex gap-2",
            option.correct ? "text-foreground" : "text-muted-foreground"
          )}
        >
          {/* Right and wrong in the scorecards' colors. */}
          {option.correct ? (
            <CheckIcon
              className={cn("mt-0.5 size-4 shrink-0", gradeTone(true))}
              role="img"
              aria-label={t("correct")}
            />
          ) : (
            <XIcon
              className={cn("mt-0.5 size-4 shrink-0", gradeTone(false))}
              role="img"
              aria-label={t("wrong")}
            />
          )}
          <span className="bidi-auto">
            <InlineText text={option.answer} />
            {picked?.includes(index) && (
              <span className="ms-2 text-muted-foreground">
                {t("yourAnswer")}
              </span>
            )}
          </span>
        </li>
      ))}
    </ul>
  )
}
