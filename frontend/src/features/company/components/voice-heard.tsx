import { useTranslations } from "next-intl"
import type { Ref } from "react"

import { YOU_BARS } from "@/config/voice"
import { FLAT } from "@/features/company/components/mira-wave"
import { TalkingDot } from "@/features/company/components/talking-dot"
import type { VoiceStatus } from "@/types/round"
import { bdi } from "@/lib/bidi"

/** The candidate's part of the voice screen: "You" with a green dot while it's their turn to
 * speak and, under it, the words Mira heard in their last answer; the wave of their own voice
 * (flat while they're silent, Mira's size in grey); under it a failure the service gave. */
export function VoiceHeard({
  waveRef,
  heard,
  problem,
  status,
}: {
  // The wave's bars, moved by useVoiceWaves.
  waveRef: Ref<HTMLDivElement>
  heard: string | null
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
      {/* Named like Mira, so the two voices read as a pair; under the name, in the room of her
          "AI interviewer" pill, the words heard in the last answer, so the two waves line up. */}
      <div className="flex flex-col items-center gap-2">
        <p className="flex items-baseline gap-2">
          <span className="relative font-heading text-2xl font-medium normal-case max-sm:text-xl">
            {t("voiceYou")}
            <TalkingDot talking={listening} />
          </span>
        </p>
        <p className="flex h-7 max-w-full items-center justify-center text-sm">
          <span className="truncate">
            {heard && t.rich("voiceHeard", { words: heard, ...bdi })}
          </span>
        </p>
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
