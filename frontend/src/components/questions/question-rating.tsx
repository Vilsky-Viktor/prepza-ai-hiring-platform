"use client"

import { cn } from "cn"
import { ThumbsDownIcon, ThumbsUpIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { FEEDBACK_HOVER_CLASS } from "@/constants/feedback"
import { apiFetch } from "@/lib/api"

type Thumb = 1 | -1

export function QuestionRating({ basePath }: { basePath: string }) {
  const t = useTranslations("questions")
  const [value, setValue] = useState<Thumb | null>(null)
  const [saving, setSaving] = useState(false)
  // Set once the user votes, so a slow load of the saved vote doesn't overwrite theirs.
  const voted = useRef(false)

  useEffect(() => {
    voted.current = false
    apiFetch<{ value: Thumb | null }>(`${basePath}/rating`)
      .then((body) => {
        if (!voted.current) {
          setValue(body.value)
        }
      })
      .catch(() => {})
  }, [basePath])

  // Voting again switches the vote.
  async function rate(next: Thumb) {
    if (saving || next === value) {
      return
    }

    const previous = value
    voted.current = true
    setValue(next)
    setSaving(true)

    try {
      await apiFetch(`${basePath}/rating`, {
        method: "PUT",
        body: JSON.stringify({ value: next }),
      })
    } catch {
      setValue(previous)
      toast.error(t("ratingFailed"))
    } finally {
      setSaving(false)
    }
  }

  const locked = saving

  return (
    <div className="contents">
      <Button
        type="button"
        variant="ghost"
        size="icon-lg"
        aria-label={t("helpful")}
        className={cn(FEEDBACK_HOVER_CLASS, "h-full w-full rounded-none")}
        aria-pressed={value === 1}
        disabled={locked}
        onClick={() => rate(1)}
      >
        <ThumbsUpIcon
          className={cn("size-6", value === 1 && "fill-primary text-primary")}
        />
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon-lg"
        aria-label={t("unhelpful")}
        className={cn(FEEDBACK_HOVER_CLASS, "h-full w-full rounded-none")}
        aria-pressed={value === -1}
        disabled={locked}
        onClick={() => rate(-1)}
      >
        <ThumbsDownIcon
          className={cn("size-6", value === -1 && "fill-primary text-primary")}
        />
      </Button>
    </div>
  )
}
