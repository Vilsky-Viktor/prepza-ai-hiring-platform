import { ACK_MIN_VOICED_MS } from "@/config/voice"
import { clipUrl, playUrl } from "@/lib/voice-clips"

/** Mira's "Got it.", said the moment a stretch of speech is sent, unless it was too short to be
 * words (a cough): fetched once and kept for the interview (the same clip in every section), so
 * it starts at once. */
export function acknowledgement() {
  let url: Promise<string> | null = null

  function load(sessionId: string) {
    url ??= clipUrl(`${sessionId}/voice/phrases/got-it`)
    // Fetched again next time if this one failed.
    url.catch(() => {
      url = null
    })

    return url
  }

  return {
    load,
    /** Plays it to its end on `player` after `voicedMs` of sound; never throws, as the answer
     * goes on without it. */
    play: async (
      player: HTMLAudioElement,
      sessionId: string,
      voicedMs: number
    ) => {
      if (voicedMs < ACK_MIN_VOICED_MS) {
        return
      }

      try {
        await playUrl(player, await load(sessionId))
      } catch (error) {
        console.warn("Mira's acknowledgement didn't play", error)
      }
    },
    release: () => {
      void url
        ?.then((address) => URL.revokeObjectURL(address))
        .catch(() => undefined)
      url = null
    },
  }
}
