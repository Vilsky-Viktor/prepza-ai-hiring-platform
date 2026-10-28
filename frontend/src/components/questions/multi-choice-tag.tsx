"use client"

import { SquareStackIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { Badge } from "@/components/ui/badge"

/** The tag on a multi-answer question, wherever it's shown: playing it, in a list, in results. */
export function MultiChoiceTag() {
  const t = useTranslations("questions")

  return (
    <Badge
      variant="outline"
      data-testid="multi-choice"
      className="h-7 px-3 text-sm font-light"
    >
      <SquareStackIcon
        aria-hidden
        data-icon="inline-start"
        className="text-primary"
      />
      {t("multiChoice")}
    </Badge>
  )
}
