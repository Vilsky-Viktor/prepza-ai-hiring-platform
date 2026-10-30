"use client"

import { cn } from "cn"
import { CornerRightDownIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { ChoiceOptions } from "@/features/company/components/choice-options"
import { CodeEditor } from "@/components/common/code-editor"
import { MultiChoiceTag } from "@/components/common/multi-choice-tag"
import { CARD_PADDING } from "@/config/cards"
import type { DemoQuestion } from "@/config/candidates-demo"
import type { CodeToken } from "@/lib/code-tokens"

// Nothing happens on a tap: the pointer plays the picks.
const NO_TAP = () => {}

/** A question and its options as a candidate plays it (features/company/components/
 * session-play.tsx), for the landing: the grey card, with the multi-answer tag on a multi-answer
 * question; its example under it in the editor's look (`exampleColors`); the hint to pick several
 * and the real option cards, the `picked` ones marked. The options are the pointer's. */
export function DemoQuestionCard({
  question,
  picked,
  exampleColors = null,
  className,
}: {
  question: DemoQuestion
  picked: number[]
  exampleColors?: CodeToken[][] | null
  className?: string
}) {
  const t = useTranslations("session")

  return (
    <div className={cn("grid grid-cols-[minmax(0,1fr)] gap-5", className)}>
      <div className="space-y-3">
        <div className={cn("space-y-3 rounded-xl bg-surface", CARD_PADDING)}>
          {question.multi && <MultiChoiceTag />}
          <p className="text-xl leading-snug font-normal">{question.text}</p>
        </div>
        {question.example && (
          <CodeEditor
            code={question.example.code}
            language={question.example.language}
            tokens={[exampleColors]}
            header={false}
            className="[&_pre]:py-2.5 [&_pre]:text-xs [&_pre]:leading-normal"
          />
        )}
      </div>
      <div className="space-y-4">
        {question.multi && (
          <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
            {t("selectAll")}
            <CornerRightDownIcon className="size-4 text-primary rtl:-scale-x-100" />
          </p>
        )}
        <div
          data-demo-target="options"
          className="[&_button]:py-2.5 [&_button]:text-base"
        >
          <ChoiceOptions
            options={question.options}
            chosen={picked}
            multi={question.multi}
            disabled={false}
            onChoose={NO_TAP}
          />
        </div>
      </div>
    </div>
  )
}
