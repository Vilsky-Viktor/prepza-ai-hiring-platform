"use client"

import { cn } from "cn"
import { PlusIcon, XIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useId, useState } from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { MAX_TOPIC_NAME_LENGTH } from "@/constants/limits"
import type { DraftTopic } from "@/types/generation"
import { bdiText } from "@/lib/bidi"

type TopicEditorProps = {
  topic: DraftTopic
  maxSubtopics: number
  onChange: (topic: DraftTopic) => void
  onDone: () => void
}

/** Rename a topic and change its subtopics by hand, without asking the model. */
export function TopicEditor({
  topic,
  maxSubtopics,
  onChange,
  onDone,
}: TopicEditorProps) {
  const t = useTranslations("generation")
  const nameError = useId()
  const [newSubtopic, setNewSubtopic] = useState("")
  const name = topic.main_topic.trim()
  const full = topic.subtopics.length >= maxSubtopics

  function addSubtopic() {
    const subtopic = newSubtopic.trim()

    if (subtopic && !full && !topic.subtopics.includes(subtopic)) {
      onChange({ ...topic, subtopics: [...topic.subtopics, subtopic] })
    }

    setNewSubtopic("")
  }

  function removeSubtopic(index: number) {
    onChange({
      ...topic,
      subtopics: topic.subtopics.filter((_, item) => item !== index),
    })
  }

  return (
    <div className="space-y-4 p-6">
      <div>
        <Input
          maxLength={MAX_TOPIC_NAME_LENGTH}
          value={topic.main_topic}
          onChange={(event) =>
            onChange({ ...topic, main_topic: event.target.value })
          }
          aria-label={t("topicName")}
          aria-invalid={!name}
          aria-describedby={name ? undefined : nameError}
          className="h-10 font-medium"
          autoFocus
        />
        {/* Always there, so a screen reader hears it as the name is cleared. */}
        <p
          id={nameError}
          role="status"
          className={cn("text-sm text-destructive", !name && "mt-2")}
        >
          {!name && t("topicNameNeeded")}
        </p>
      </div>

      <ul className="flex flex-wrap gap-2">
        {topic.subtopics.map((subtopic, index) => (
          <li
            key={subtopic}
            className="flex items-center gap-1 rounded-full bg-muted py-1 ps-3 pe-1 text-sm"
          >
            {subtopic}
            <Button
              type="button"
              variant="ghost"
              size="icon-xs"
              className="rounded-full"
              aria-label={t.markup("removeSubtopic", { subtopic, ...bdiText })}
              onClick={() => removeSubtopic(index)}
            >
              <XIcon />
            </Button>
          </li>
        ))}
      </ul>

      <div className="flex items-center gap-2">
        <Input
          maxLength={MAX_TOPIC_NAME_LENGTH}
          value={newSubtopic}
          onChange={(event) => setNewSubtopic(event.target.value)}
          onKeyDown={(event) => {
            // Enter adds the subtopic instead of submitting the review.
            if (event.key === "Enter") {
              event.preventDefault()
              addSubtopic()
            }
          }}
          placeholder={
            full
              ? t("subtopicsFull", { count: maxSubtopics })
              : t("addSubtopic")
          }
          aria-label={t("newSubtopic")}
          disabled={full}
          className="h-10"
        />
        <Button
          type="button"
          variant="outline"
          className="h-10 px-3"
          disabled={full || !newSubtopic.trim()}
          onClick={addSubtopic}
        >
          <PlusIcon />
          {t("add")}
        </Button>
        <Button
          type="button"
          variant="secondary"
          className="h-10 px-4"
          disabled={!name}
          onClick={onDone}
        >
          {t("done")}
        </Button>
      </div>
    </div>
  )
}
