import { useTranslations } from "next-intl"
import type { Ref } from "react"

import { YOU_BARS } from "@/config/voice"
import { FLAT } from "@/features/company/components/mira-wave"
import { TalkingDot } from "@/features/company/components/talking-dot"
import type { VoiceStatus } from "@/types/round"

/** The candidate's part of the voice screen: "You" with a green dot while it's their turn to
 * speak and a "candidate" pill under it; the wave of their own voice (flat while they're silent,
 * Mira's size in grey); under it a failure the service gave. */
export function VoiceHeard({
  waveRef,
  problem,
  status,
}: {
  // The wave's bars, moved by useVoiceWaves.
  waveRef: Ref<HTMLDivElement>
  problem: string | null
  status: VoiceStatus
}) {
  const t = useTranslations("session")
  // The microphone takes an answer now: Mira isn't speaking or thinking.
  const listening = status === "listening" || status === "hearing"

  return (
    <div
      className="flex w-full flex-col items-center gap-5 max-sm:gap-3"
      data-testid="voice-heard"
    >
      {/* Named like Mira, so the two voices read as a pair. */}
      <div className="flex flex-col items-center gap-2">
        <p className="flex items-baseline gap-2">
          <span className="relative font-heading text-2xl font-medium normal-case max-sm:text-xl">
            {t("voiceYou")}
            <TalkingDot talking={listening} />
          </span>
        </p>
        {/* A pill like Mira's "AI interviewer", so the two sides read as a pair and line up. */}
        <span className="flex h-7 items-center">
          <span className="rounded-full border px-2.5 py-0.5 text-xs text-muted-foreground">
            {t("voiceCandidate")}
          </span>
        </span>
      </div>
      <span
        ref={waveRef}
        aria-hidden
        className="flex h-24 w-full items-center justify-between max-sm:h-10"
      >
        {Array.from({ length: YOU_BARS }, (_, index) => (
          <span
            key={index}
            style={FLAT}
            className="h-full w-1.5 rounded-full bg-muted-foreground will-change-transform"
          />
        ))}
      </span>
      <p
        role="status"
        // Empty, it takes no room (still there for screen readers), so the line under the waves
        // sits close.
        className="text-sm whitespace-pre-line text-destructive empty:sr-only"
      >
        {problem}
      </p>
    </div>
  )
}
