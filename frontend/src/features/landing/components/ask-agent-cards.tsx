"use client"

import { BookOpenIcon, ChartColumnIcon, ZapIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { GLOW_CARD } from "@/config/landing-backgrounds"

import { IconCard, PHONE_CARDS } from "@/features/landing/components/icon-card"
import { ASK_AGENT_CARDS } from "@/config/ask-agent-demo"

const ICONS = {
  info: ChartColumnIcon,
  help: BookOpenIcon,
  actions: ZapIcon,
}

/** What the agent does, as grey cards beside its chat; the one the chat is showing (`lit`)
 * ringed. On phones, without the chat, edge to edge. */
export function AskAgentCards({ lit }: { lit?: string }) {
  const t = useTranslations("landing.justAsk")

  return (
    <ul className={`grid gap-3 md:grid-rows-3 ${PHONE_CARDS}`}>
      {ASK_AGENT_CARDS.map((key) => (
        <IconCard
          key={key}
          icon={ICONS[key]}
          title={t(`cards.${key}.title`)}
          lit={lit === key}
          className={GLOW_CARD}
        >
          {t(`cards.${key}.text`)}
        </IconCard>
      ))}
    </ul>
  )
}
