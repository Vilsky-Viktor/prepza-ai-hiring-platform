"use client"

import { BookOpenIcon, ChartColumnIcon, ZapIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { IconCard } from "@/components/landing/icon-card"
import { ASK_AGENT_CARDS } from "@/config/ask-agent-demo"

const ICONS = {
  info: ChartColumnIcon,
  help: BookOpenIcon,
  actions: ZapIcon,
}

/** What the agent does, as grey cards beside its chat; the one the chat is showing (`lit`)
 * ringed. */
export function AskAgentCards({ lit }: { lit?: string }) {
  const t = useTranslations("landing.justAsk")

  return (
    <ul className="grid gap-3 md:grid-rows-3">
      {ASK_AGENT_CARDS.map((key) => (
        <IconCard
          key={key}
          icon={ICONS[key]}
          title={t(`cards.${key}.title`)}
          lit={lit === key}
        >
          {t(`cards.${key}.text`)}
        </IconCard>
      ))}
    </ul>
  )
}
