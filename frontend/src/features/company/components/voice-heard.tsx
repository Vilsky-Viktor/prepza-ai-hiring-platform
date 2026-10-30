import { MicIcon, MicOffIcon } from "lucide-react"
import { useTranslations } from "next-intl"
import type { Ref } from "react"

import { Button } from "@/components/ui/button"
import { YOU_BARS } from "@/config/voice"
import { FLAT } from "@/features/company/components/mira-wave"
import { TalkingDot } from "@/features/company/components/talking-dot"
import type { VoiceStatus } from "@/types/round"
import { bdi } from "@/lib/bidi"

/** The candidate's part of the voice screen: "You" with a green dot while it's their turn to
 * speak, the wave of their own voice (flat while they're silent or muted, Mira's size in grey),
 * Mute while the microphone takes an answer, the words Mira heard in their last answer, and under
 * them a failure the service gave. */
export function VoiceHeard({
  waveRef,
  heard,
  problem,
  status,
  muted,
  onToggleMute,
}: {
  // The wave's bars, moved by useVoiceWaves.
  waveRef: Ref<HTMLDivElement>
  heard: string | null
  problem: string | null
  status: VoiceStatus
  muted: boolean
  onToggleMute: () => void
}) {
  const t = useTranslations("session")
  // The microphone takes an answer now: not muted, and Mira isn't speaking or thinking.
  const listening = !muted && (status === "listening" || status === "hearing")

  return (
    <div
      className="flex w-full flex-col items-center gap-5 max-sm:gap-3"
      data-testid="voice-heard"
    >
      {/* Named like Mira above, so the two voices read as a pair. */}
      <p className="flex items-baseline gap-2">
        <span className="relative font-heading text-2xl font-medium normal-case max-sm:text-xl">
          {t("voiceYou")}
          <TalkingDot talking={listening} />
        </span>
      </p>
      <span
        ref={waveRef}
        aria-hidden
        className="flex h-24 w-full items-center justify-between max-sm:h-14"
      >
        {Array.from({ length: YOU_BARS }, (_, index) => (
          <span
            key={index}
            style={FLAT}
            className="h-full w-1.5 rounded-full bg-muted-foreground will-change-transform"
          />
        ))}
      </span>
      {/* Mute only while the microphone takes an answer; muted, the way to turn it back on. */}
      {(listening || muted) && (
        <Button
          variant="outline"
          className="h-10 px-5 text-base"
          onClick={onToggleMute}
          data-testid="voice-mute"
        >
          {muted ? <MicIcon aria-hidden /> : <MicOffIcon aria-hidden />}
          {muted ? t("voiceUnmute") : t("voiceMute")}
        </Button>
      )}
      {/* The answer heard, on its own line under the wave. */}
      <p className="min-h-6 text-base break-words">
        {heard && t.rich("voiceHeard", { words: heard, ...bdi })}
      </p>
      <p role="status" className="text-sm whitespace-pre-line text-destructive">
        {problem}
      </p>
    </div>
  )
}
