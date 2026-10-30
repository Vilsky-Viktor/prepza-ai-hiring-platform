import { ApiError, authHeaders, errorDetail } from "@/lib/api"
import type { VoiceAnswer } from "@/types/round"

async function checked(response: Response) {
  if (!response.ok) {
    const detail = errorDetail(await response.json().catch(() => null))

    throw new ApiError(
      response.status,
      detail ?? `Request failed with status ${response.status}`,
      detail !== null
    )
  }

  return response
}

/** A clip the interviewer says (the question, a phrase), as an address the page can play; the
 * caller revokes it once played. */
export async function clipUrl(path: string): Promise<string> {
  const response = await checked(
    await fetch(`/api/rounds/sessions/${path}`, {
      headers: await authHeaders(),
    })
  )

  return URL.createObjectURL(await response.blob())
}

/** Plays `path`'s clip on `player` and resolves when it has ended; rejects when it can't be
 * fetched or played. A clip cut off (another one started, or voice mode stopped) never resolves,
 * so what was to follow it doesn't happen. */
export async function playClip(player: HTMLAudioElement, path: string) {
  const url = await clipUrl(path)

  try {
    await playUrl(player, url)
  } finally {
    URL.revokeObjectURL(url)
  }
}

/** Plays a clip's address on `player`, as playClip does, leaving the address to the caller. */
export function playUrl(player: HTMLAudioElement, url: string) {
  player.src = url

  return new Promise<void>((done, failed) => {
    player.onended = () => done()
    player.onerror = () => failed(player.error)
    player.play().catch(failed)
  })
}

/** Asks the service to read the section's next question aloud ahead, as the question on screen
 * opens, so moving on doesn't wait for it; nothing of it comes back. Best effort: a failure only
 * means that question is read when it opens. */
export function prepareNextQuestion(sessionId: string) {
  void authHeaders()
    .then((headers) =>
      fetch(`/api/rounds/sessions/${sessionId}/voice/next-question/prepare`, {
        method: "POST",
        headers,
      })
    )
    .catch(() => undefined)
}

/** A spoken answer to the question on screen, understood by the service: what it heard, what it
 * meant and the options it picks. `waiting` is the choice on screen, which a yes confirms. */
export async function sendSpokenAnswer(
  sessionId: string,
  audio: Blob,
  waiting: number[]
): Promise<VoiceAnswer> {
  const query = new URLSearchParams(
    waiting.map((pick) => ["waiting", String(pick)])
  )
  const response = await checked(
    await fetch(`/api/rounds/sessions/${sessionId}/voice/answers?${query}`, {
      method: "POST",
      headers: { ...(await authHeaders()), "Content-Type": audio.type },
      body: audio,
    })
  )

  return response.json()
}
