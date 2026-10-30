import { useTranslations } from "next-intl"

import type { VoiceStatus } from "@/types/round"

/** The line between Mira's part of the voice screen and the candidate's, fading out towards both
 * ends, with a pill over its middle saying whose turn it is: the candidate's while the microphone
 * listens, "Thinking" (a light running along the line) while Mira works out what she heard, and
 * Mira's otherwise. */
export function VoiceTurn({ status }: { status: VoiceStatus }) {
  const t = useTranslations("session")
  const yours = status === "listening" || status === "hearing"
  const turn = yours ? "candidate" : status === "thinking" ? "thinking" : "mira"
  const label = {
    candidate: t("voiceYourTurn"),
    thinking: t("voiceThinking"),
    mira: t("voiceMiraTurn"),
  }[turn]

  return (
    <div
      aria-hidden
      data-testid="voice-turn"
      data-turn={turn}
      className="relative flex items-center justify-center"
    >
      <span
        // The light runs the same way in every language: the line shows no direction.
        dir="ltr"
        className="absolute inset-x-0 h-0.5 overflow-hidden rounded-full bg-linear-to-r from-transparent via-muted-foreground/50 to-transparent"
      >
        {/* While Mira thinks, a primary light glides slowly from the line's start to its end and
            back. */}
        {turn === "thinking" && (
          <span className="absolute inset-y-0 start-0 w-1/3 animate-[line-sweep_2.4s_ease-in-out_infinite_alternate] bg-linear-to-r from-transparent via-primary to-transparent" />
        )}
      </span>
      <span className="relative rounded-full border bg-background px-3 py-1 text-sm">
        {label}
      </span>
    </div>
  )
}
