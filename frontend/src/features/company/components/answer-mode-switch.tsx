"use client"

import { MicIcon, MousePointerClickIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { Button } from "@/components/ui/button"
import { CARD_PADDING } from "@/config/cards"

const MODES = [
  { voice: false, key: "clickMode", icon: MousePointerClickIcon },
  { voice: true, key: "voiceMode", icon: MicIcon },
] as const

/** How an interview is taken, click mode or voice mode, as one switch the height of a field:
 * two halves of one grey field, the chosen half filled like the primary button, edge to edge.
 * The interview's settings, the invite dialog and a candidate's page share it. */
export function AnswerModeSwitch({
  label,
  voice,
  disabled,
  onChange,
}: {
  label: string
  voice: boolean
  disabled: boolean
  onChange: (voice: boolean) => void
}) {
  const t = useTranslations("interviews")

  return (
    <div
      role="group"
      aria-label={label}
      className="flex h-14 shrink-0 overflow-hidden rounded-xl bg-surface max-sm:w-full"
    >
      {MODES.map(({ voice: option, key, icon: Icon }) => (
        <Button
          key={key}
          type="button"
          variant={voice === option ? "default" : "ghost"}
          aria-pressed={voice === option}
          disabled={disabled}
          className="h-full min-w-28 gap-2 rounded-none border-0 px-4 text-base text-muted-foreground hover:bg-transparent aria-pressed:text-primary-foreground max-sm:flex-1 [&_svg:not([class*='size-'])]:size-5"
          onClick={() => voice !== option && onChange(option)}
        >
          <Icon aria-hidden />
          {t(key)}
        </Button>
      ))}
    </div>
  )
}

/** The mode as a row of a settings list: its name, a line under it, and the switch beside them
 * (on phones the switch takes its own line, full width). */
export function AnswerModeSetting({
  label,
  help,
  ...change
}: {
  label: string
  help: string
  voice: boolean
  disabled: boolean
  onChange: (voice: boolean) => void
}) {
  return (
    <div
      className={`flex items-center justify-between gap-4 max-sm:flex-col max-sm:items-stretch ${CARD_PADDING}`}
    >
      <span className="min-w-0 space-y-1">
        <span className="block text-lg font-light">{label}</span>
        <span className="block text-sm text-muted-foreground">{help}</span>
      </span>
      <AnswerModeSwitch label={label} {...change} />
    </div>
  )
}
