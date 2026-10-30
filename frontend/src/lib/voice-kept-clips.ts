import { clipUrl, playClip, playUrl } from "@/lib/voice-clips"

/** Mira's short clips (her phrases, "B, saved."), fetched ahead and kept in the page for the
 * interview, so none is fetched the moment it's said: by the clip's path after the session
 * ("phrases/unclear"), the same in every section. A few seconds of Opus each, released at the
 * end. */
export function keptClips() {
  const urls = new Map<string, Promise<string>>()

  /** The clip's address, fetched now unless kept; fetched again next time if this one fails. */
  function load(sessionId: string, clip: string) {
    const kept = urls.get(clip)

    if (kept) {
      return kept
    }

    const url = clipUrl(`${sessionId}/voice/${clip}`)
    urls.set(clip, url)
    url.catch(() => {
      if (urls.get(clip) === url) {
        urls.delete(clip)
      }
    })

    return url
  }

  return {
    load,
    /** Plays the clip at `path` ("<session>/voice/phrases/unclear") on `player` as playClip
     * does: from the page when it's kept, fetched otherwise. */
    play: async (player: HTMLAudioElement, path: string) => {
      const kept = urls.get(path.replace(/^[^/]+\/voice\//, ""))

      return kept ? playUrl(player, await kept) : playClip(player, path)
    },
    /** Fetches each clip ahead; best effort, as a clip not kept is fetched when it's said. */
    preload: (sessionId: string, clips: string[]) => {
      for (const clip of clips) {
        void load(sessionId, clip).catch(() => undefined)
      }
    },
    release: () => {
      for (const url of urls.values()) {
        void url
          .then((address) => URL.revokeObjectURL(address))
          .catch(() => undefined)
      }

      urls.clear()
    },
  }
}

/** A question's "{letter}, saved." clips, by their path after the session, for its first
 * `letters` options. */
export function savedClips(letters: number) {
  return Array.from({ length: letters }, (_, pick) => `saved/${pick}`)
}

export type KeptClips = ReturnType<typeof keptClips>
