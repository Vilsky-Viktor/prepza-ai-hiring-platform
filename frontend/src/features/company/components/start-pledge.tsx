"use client"

import { useTranslations } from "next-intl"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { START_BUTTON } from "@/config/start-page"
import { VoiceAccessStep } from "@/features/company/components/voice-access-step"
import { useVoiceAccess } from "@/hooks/use-voice-access"

/** An interview's start button, with the candidate's pledge to answer on their own above it: the
 * start works once it's ticked, and the start request carries it (the API refuses a first start
 * without it). Continuing an interview already started (`pledge` false) needs none. A voice
 * interview (`voice`) first asks for the microphone and sound: the start works once allowed. */
export function StartPledge({
  label,
  pledge,
  busy,
  onStart,
  testId,
  voice = false,
}: {
  label: string
  pledge: boolean
  busy: boolean
  onStart: (pledged: boolean) => void
  testId?: string
  voice?: boolean
}) {
  const t = useTranslations("invite")
  const [pledged, setPledged] = useState(false)
  const { access, allow } = useVoiceAccess(voice)
  const waiting = voice && access !== "granted"

  return (
    <div className="space-y-6">
      {voice && <VoiceAccessStep access={access} onAllow={allow} />}
      {/* As the sign-in's email choices: the box and its line, the whole line ticks it. */}
      {pledge && (
        <label className="mx-auto flex w-fit cursor-pointer items-center gap-3 text-start text-sm">
          <Checkbox
            className="size-5 shrink-0 [&_[data-slot=checkbox-indicator]>svg]:size-3.5"
            checked={pledged}
            disabled={busy}
            data-testid="start-pledge"
            onCheckedChange={setPledged}
          />
          {t("pledge")}
        </label>
      )}
      <Button
        className={START_BUTTON}
        disabled={busy || waiting || (pledge && !pledged)}
        data-testid={testId}
        onClick={() => onStart(pledged)}
      >
        {label}
      </Button>
    </div>
  )
}
