"use client"

import { useTranslations } from "next-intl"
import { useState } from "react"

import { Badge } from "@/components/ui/badge"

// Tags shown before "+N more".
const SHOWN = 3
const TAG = "h-7 px-3 text-sm font-light text-muted-foreground"

/** A topic's subtopics as quiet tags: the first few, then a "+N more" tag that shows the rest. */
export function SubtopicList({ subtopics }: { subtopics: string[] }) {
  const t = useTranslations("questions")
  const [expanded, setExpanded] = useState(false)
  const hidden = subtopics.length - SHOWN
  const shown = expanded || hidden <= 0 ? subtopics : subtopics.slice(0, SHOWN)

  if (subtopics.length === 0) {
    return null
  }

  return (
    <span className="flex flex-wrap gap-2">
      {shown.map((subtopic) => (
        <Badge
          key={subtopic}
          variant="outline"
          className={`${TAG} normal-case`}
        >
          {subtopic}
        </Badge>
      ))}
      {hidden > 0 && (
        <button
          type="button"
          className="h-7 cursor-pointer px-1 text-sm text-primary transition-opacity hover:opacity-70"
          aria-expanded={expanded}
          onClick={() => setExpanded((current) => !current)}
        >
          {expanded ? t("showLess") : t("more", { count: hidden })}
        </button>
      )}
    </span>
  )
}
