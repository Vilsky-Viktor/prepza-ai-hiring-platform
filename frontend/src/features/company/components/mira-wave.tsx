import { cn } from "cn"
import { Volume2Icon } from "lucide-react"
import { useTranslations } from "next-intl"
import type { Ref } from "react"

import { Button } from "@/components/ui/button"
import { TalkingDot } from "@/features/company/components/talking-dot"
import { FLAT_BAR, MIRA_BARS } from "@/config/voice"
import type { VoiceStatus } from "@/types/round"

// A bar's resting height: a flat line, as useVoiceWaves leaves it in silence.
export const FLAT = { transform: `scaleY(${FLAT_BAR})` }

/** Mira, the AI interviewer, on the voice screen: her name, labelled as AI, with a green dot while
 * she speaks, the wave her voice moves (flat while she's silent), and what she's doing, read out
 * politely to screen readers as it changes (once an answer is `picked`, how to confirm or change
 * it). A page reloaded without a tap gets the button that turns her sound on. */
export function MiraWave({
  waveRef,
  status,
  picked,
  onSoundOn,
}: {
  // The wave's bars, moved by useVoiceWaves.
  waveRef: Ref<HTMLDivElement>
  status: VoiceStatus
  // An answer is chosen and waits for a yes, or another answer.
  picked: boolean
  onSoundOn: () => void
}) {
  const t = useTranslations("session")
  function statusText() {
    return status === "listening" && picked
      ? t("voiceStatus.listeningPicked")
      : t(`voiceStatus.${status}`)
  }

  return (
    <div className="flex w-full flex-col items-center gap-5 max-sm:gap-3">
      {/* Her name with the green dot, and under it the pill saying she's an AI interviewer. */}
      <div className="flex flex-col items-center gap-2">
        <p className="flex items-baseline gap-2">
          <span className="relative font-heading text-2xl font-medium normal-case max-sm:text-xl">
            {t("miraName")}
            <TalkingDot talking={status === "speaking"} />
          </span>
        </p>
        {/* The same height as the words heard under "You", so the two sides line up. */}
        <span className="flex h-7 items-center">
          <span className="rounded-full border px-2.5 py-0.5 text-xs text-muted-foreground">
            {t("miraLabel")}
          </span>
        </span>
      </div>
      <div
        ref={waveRef}
        aria-hidden
        data-testid="mira-wave"
        className="flex h-24 w-full items-center justify-between max-sm:h-10"
      >
        {Array.from({ length: MIRA_BARS }, (_, index) => (
          <span
            key={index}
            style={FLAT}
            className="h-full w-1.5 rounded-full bg-primary will-change-transform"
          />
        ))}
      </div>
      {/* What she's doing is read out to screen readers; on screen the green dot shows it, and
          only a problem (sound held back, no microphone) is written. */}
      <p
        role="status"
        data-testid="voice-status"
        className={cn(
          "max-w-xl text-base text-foreground",
          status !== "blocked" && status !== "unavailable" && "sr-only"
        )}
      >
        {statusText()}
      </p>
      {status === "blocked" && (
        <Button className="h-12 px-6 text-base" onClick={onSoundOn}>
          <Volume2Icon aria-hidden />
          {t("voiceSoundOn")}
        </Button>
      )}
    </div>
  )
}
