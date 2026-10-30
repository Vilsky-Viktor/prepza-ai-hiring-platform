"use client"

import { MicIcon, MousePointerClickIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { IconStat } from "@/components/common/icon-stat"

/** How an interview is answered, as an icon named in its tooltip: voice mode (read aloud,
 * answered by voice) or click mode, the default. */
export function AnswerModeIcon({
  voice,
  className,
}: {
  voice: boolean
  className?: string
}) {
  const t = useTranslations("interviews")
  const Icon = voice ? MicIcon : MousePointerClickIcon

  return (
    <IconStat
      label={voice ? t("voiceModeIcon") : t("clickModeIcon")}
      icon={<Icon aria-hidden className="size-5" />}
      className={className}
      data-testid="answer-mode"
      data-mode={voice ? "voice" : "click"}
    />
  )
}
