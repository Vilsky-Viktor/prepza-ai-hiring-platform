"use client"

import { SquarePenIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import type { ReactNode } from "react"
import { useState } from "react"

import { TopicEditor } from "@/features/generation/components/topic-editor"
import { RoundFooter } from "@/components/session/round-footer"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Textarea } from "@/components/ui/textarea"
import { MAX_INSTRUCTIONS_LENGTH } from "@/config/limits"
import type { DraftTopic } from "@/types/generation"
import { LIST_BOX } from "@/config/lists"
import { Dot } from "@/components/common/dot"
import { bdiText } from "@/lib/bidi"

type TopicReviewProps = {
  topics: DraftTopic[]
  maxTopics: number
  // Subtopics a topic may have when edited by hand.
  maxSubtopics: number
  back: ReactNode
  // Shown at the left of the submit row.
  cancel?: ReactNode
  // `edited` is every topic with the reviewer's own changes, or null when nothing was edited.
  onSubmit: (
    selected: number[],
    instructions: string,
    edited: DraftTopic[] | null
  ) => Promise<void>
}

export function TopicReview({
  topics,
  maxTopics,
  maxSubtopics,
  back,
  cancel,
  onSubmit,
}: TopicReviewProps) {
  const t = useTranslations("generation")
  const common = useTranslations("common")
  const [selected, setSelected] = useState(() =>
    topics.map((_, index) => index)
  )
  const [draft, setDraft] = useState(topics)
  const [editing, setEditing] = useState<number | null>(null)
  const [instructions, setInstructions] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const edited = JSON.stringify(draft) !== JSON.stringify(topics)
  const unnamed = draft.some((topic) => !topic.main_topic.trim())
  const revising =
    instructions.trim().length > 0 || selected.length !== topics.length
  // Without instructions the selection is approved as is, so it must fit the limit.
  const tooMany = !instructions.trim() && selected.length > maxTopics

  function toggle(index: number, checked: boolean) {
    setSelected((current) =>
      checked
        ? [...current, index].sort((a, b) => a - b)
        : current.filter((item) => item !== index)
    )
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    await onSubmit(selected, instructions.trim(), edited ? draft : null)
    setSubmitting(false)
  }

  return (
    // pb-28 keeps the last field clear of the sticky footer.
    <form onSubmit={handleSubmit} className="space-y-8 pb-28">
      <div className="space-y-2">
        <div className="relative">
          {back}
          <h1 className="font-heading text-3xl font-medium tracking-tight">
            {t("reviewTitle")}
          </h1>
        </div>
        <p className="text-muted-foreground">{t("reviewText")}</p>
      </div>

      <ul className={LIST_BOX}>
        {draft.map((topic, index) =>
          editing === index ? (
            <li key={index}>
              <TopicEditor
                topic={topic}
                maxSubtopics={maxSubtopics}
                onChange={(changed) =>
                  setDraft((current) =>
                    current.map((item, itemIndex) =>
                      itemIndex === index ? changed : item
                    )
                  )
                }
                onDone={() => setEditing(null)}
              />
            </li>
          ) : (
            <li key={index} className="relative">
              <label className="flex cursor-pointer items-center gap-5 p-6 pe-16">
                <Checkbox
                  className="size-6 shrink-0 [&_[data-slot=checkbox-indicator]>svg]:size-4"
                  checked={selected.includes(index)}
                  onCheckedChange={(checked) => toggle(index, checked)}
                />
                <span className="space-y-1">
                  <span className="block font-medium">{topic.main_topic}</span>
                  <span className="block text-sm text-muted-foreground">
                    {topic.subtopics.map((subtopic, subtopicIndex) => (
                      <span key={subtopic}>
                        {subtopicIndex > 0 && <Dot />}
                        {subtopic}
                      </span>
                    ))}
                  </span>
                </span>
              </label>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute end-4 top-1/2 -translate-y-1/2"
                aria-label={t.markup("editTopic", {
                  topic: topic.main_topic,
                  ...bdiText,
                })}
                tooltip={common("edit")}
                onClick={() => setEditing(index)}
              >
                <SquarePenIcon />
              </Button>
            </li>
          )
        )}
      </ul>

      {/* Same card as the goal input on the home page. */}
      <div className="relative w-full rounded-xl border border-transparent bg-surface p-3 transition-colors focus-within:border-ring-gradient">
        <Textarea
          maxLength={MAX_INSTRUCTIONS_LENGTH}
          value={instructions}
          onChange={(event) => setInstructions(event.target.value)}
          placeholder={t("changesPlaceholder")}
          aria-label={t("changes")}
          className="max-h-72 min-h-24 resize-none border-0 bg-transparent p-2 text-base shadow-none focus-visible:ring-0 md:text-base dark:bg-transparent"
        />
      </div>

      <RoundFooter>
        <div>{cancel}</div>
        <div className="flex items-center gap-4">
          {/* Always there, so a screen reader hears why Approve stopped working. */}
          <p role="status" className="text-sm text-destructive">
            {tooMany && t("tooMany", { max: maxTopics })}
          </p>
          <Button
            type="submit"
            className="h-12 px-6 text-base"
            disabled={selected.length === 0 || tooMany || unnamed || submitting}
          >
            {revising ? t("apply") : t("approve")}
          </Button>
        </div>
      </RoundFooter>
    </form>
  )
}
