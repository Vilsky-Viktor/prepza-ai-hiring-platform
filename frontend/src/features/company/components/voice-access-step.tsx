"use client"

import { CheckIcon, MicIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { InfoCard, WarningCard } from "@/components/common/warning-card"
import { Button } from "@/components/ui/button"
import type { VoiceAccess } from "@/hooks/use-voice-access"

// The allow button's words in each state; granted and unsupported have no button.
const BUTTON = {
  ask: "voiceAllow",
  asking: "voiceAllowing",
  denied: "voiceRetry",
} as const

/** A voice interview's first step on its start page: the microphone and sound allowed, before
 * the start button works. Refused, it says how to allow them; its changes are read out. */
export function VoiceAccessStep({
  access,
  onAllow,
}: {
  access: VoiceAccess
  onAllow: () => void
}) {
  const t = useTranslations("invite")
  const refused = access === "denied" || access === "unsupported"
  const Card = refused ? WarningCard : InfoCard

  return (
    <div
      aria-live="polite"
      data-testid="voice-access"
      data-access={access}
      className="mx-auto max-w-md space-y-4 text-start"
    >
      {access === "granted" ? (
        <p className="flex items-center justify-center gap-2 text-base text-muted-foreground">
          <CheckIcon aria-hidden className="size-5 shrink-0 text-primary" />
          {t("voiceReady")}
        </p>
      ) : (
        <Card>
          {access === "denied" && t("voiceDenied")}
          {access === "unsupported" && t("voiceUnsupported")}
          {!refused && t("voiceAccess")}
        </Card>
      )}
      {access !== "granted" && access !== "unsupported" && (
        <Button
          variant="outline"
          className="h-12 w-full px-6 text-base"
          disabled={access === "asking"}
          onClick={onAllow}
        >
          <MicIcon aria-hidden />
          {t(BUTTON[access])}
        </Button>
      )}
    </div>
  )
}
