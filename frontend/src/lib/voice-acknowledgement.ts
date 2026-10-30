import { ACK_DELAY_MS, ACK_MIN_VOICED_MS, GOT_IT_CLIP } from "@/config/voice"
import { playUrl } from "@/lib/voice-clips"
import type { KeptClips } from "@/lib/voice-kept-clips"

/** Mira's "Got it.", only to fill a wait: said when no answer is back ACK_DELAY_MS after a
 * stretch of speech was sent (not after one too short to be words, a cough), and cut off the
 * moment the answer is back, so her reaction never waits for it and two of her clips never play
 * at once (both play on the one player). */
export function acknowledgement(clips: KeptClips) {
  let timer: ReturnType<typeof setTimeout> | undefined
  // The turn it's for: a cancelled turn's clip never starts.
  let turn = 0
  // Its address while it plays, so only it is ever stopped.
  let playing: string | null = null

  return {
    /** Plays it on `player` after ACK_DELAY_MS, unless cancelled; never throws, as the answer
     * goes on without it. */
    schedule: (
      player: HTMLAudioElement,
      sessionId: string,
      voicedMs: number
    ) => {
      const mine = ++turn

      if (voicedMs < ACK_MIN_VOICED_MS) {
        return
      }

      timer = setTimeout(async () => {
        try {
          const url = await clips.load(sessionId, GOT_IT_CLIP)

          if (mine !== turn) {
            return
          }

          playing = url
          await playUrl(player, url)
        } catch (error) {
          console.warn("Mira's acknowledgement didn't play", error)
        } finally {
          if (mine === turn) {
            playing = null
          }
        }
      }, ACK_DELAY_MS)
    },
    /** The answer is back, or Mira says something else: it doesn't start, or stops where it
     * is (never another clip on the player). */
    cancel: (player: HTMLAudioElement | null) => {
      turn++
      clearTimeout(timer)

      if (playing && player?.src === playing) {
        player.pause()
      }

      playing = null
    },
  }
}
