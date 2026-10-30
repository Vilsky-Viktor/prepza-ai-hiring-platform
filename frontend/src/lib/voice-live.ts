import {
  LIVE_ANSWER_WAIT_MS,
  LIVE_MAX_FAILURES,
  LIVE_RENEW_MS,
} from "@/config/voice"

import { idToken } from "@/lib/api"
import { sendSpokenAnswer } from "@/lib/voice-clips"
import type { VoiceAnswer } from "@/types/round"

/** A spoken answer understood by the service, with its stages' milliseconds. */
export type Understood = { answer: VoiceAnswer; stages: Record<string, number> }

type Connection = {
  started: () => boolean
  start: (frames: Float32Array[]) => void
  frame: (samples: Float32Array) => void
  end: (waiting: number[]) => Promise<Understood | null>
  close: () => void
}

/** The detector's samples (-1 to 1) as 16-bit PCM, as the service takes them. */
export function pcm16(samples: Float32Array) {
  const out = new Int16Array(samples.length)

  for (let index = 0; index < samples.length; index++) {
    const sample = Math.max(-1, Math.min(1, samples[index]))
    out[index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff
  }

  return out.buffer
}

function streamUrl(sessionId: string) {
  const scheme = window.location.protocol === "https:" ? "wss" : "ws"

  return `${scheme}://${window.location.host}/api/rounds/sessions/${sessionId}/voice/stream`
}

/** One answer's connection to the service (rounds' services/voice_stream.py): signed in by its
 * first message, then `start`, the audio and `end`. What's sent before it's open waits in order.
 * `ready` once the service's transcription is ready; `failed` when it closed before that. */
function connect(
  sessionId: string,
  events: { ready: () => void; failed: () => void }
): Connection {
  const socket = new WebSocket(streamUrl(sessionId))
  let queue: (string | ArrayBuffer)[] | null = []
  let ready = false
  let started = false
  let closed = false
  let answered: ((value: Understood | null) => void) | null = null

  function send(data: string | ArrayBuffer) {
    if (closed) {
      return
    }

    if (queue) {
      queue.push(data)
    } else {
      socket.send(data)
    }
  }

  function settle(value: Understood | null) {
    answered?.(value)
    answered = null
  }

  socket.binaryType = "arraybuffer"
  socket.onopen = async () => {
    const token = await idToken().catch(() => undefined)

    if (!token || closed) {
      socket.close()

      return
    }

    socket.send(JSON.stringify({ token }))
    queue?.forEach((data) => socket.send(data))
    queue = null
  }
  socket.onmessage = (event) => {
    const message = JSON.parse(String(event.data))

    if (message.type === "ready") {
      ready = true
      events.ready()
    } else if (message.type === "answer") {
      settle({ answer: message.answer, stages: message.stages })
    }
  }
  socket.onclose = () => {
    closed = true
    settle(null)

    if (!ready) {
      events.failed()
    }
  }

  function close() {
    closed = true
    settle(null)
    socket.close()
  }

  return {
    started: () => started,
    start: (frames) => {
      started = true
      send(JSON.stringify({ type: "start" }))
      frames.forEach((frame) => send(pcm16(frame)))
    },
    frame: (samples) => {
      if (started) {
        send(pcm16(samples))
      }
    },
    end: (waiting) => {
      if (!started || closed) {
        close()

        return Promise.resolve(null)
      }

      const result = new Promise<Understood | null>((resolve) => {
        answered = resolve
      })
      const timer = setTimeout(close, LIVE_ANSWER_WAIT_MS)
      send(JSON.stringify({ type: "end", waiting }))

      return result.finally(() => {
        clearTimeout(timer)
        close()
      })
    },
    close,
  }
}

/** Voice mode's live listening, the listener's live sink (lib/voice-listening.ts): a connection
 * opened as listening starts (open), the candidate's speech sent as it comes once they're heard
 * (start, frame), and its end sent with the choice waiting on screen (end). `answer(recording)`
 * then gives that answer, or, when it wasn't heard live, the recording's, sent whole. `latest`
 * holds the session and the choice on screen now. A quiet connection is renewed after
 * LIVE_RENEW_MS; after LIVE_MAX_FAILURES that never got ready in a row, none is opened again. */
export function liveListening(latest: {
  current: { sessionId: string; chosen: number[] }
}) {
  let current: Connection | null = null
  let renew: ReturnType<typeof setTimeout> | undefined
  let failures = 0
  let ended: Promise<Understood | null> | null = null

  function close() {
    clearTimeout(renew)
    current?.close()
    current = null
  }

  function open() {
    close()

    if (failures >= LIVE_MAX_FAILURES) {
      return
    }

    const mine = connect(latest.current.sessionId, {
      ready: () => {
        failures = 0
      },
      failed: () => {
        failures++
      },
    })
    current = mine
    renew = setTimeout(() => {
      if (current === mine && !mine.started()) {
        open()
      }
    }, LIVE_RENEW_MS)
  }

  return {
    open,
    close,
    start: (frames: Float32Array[]) => current?.start(frames),
    frame: (samples: Float32Array) => current?.frame(samples),
    // The answer's connection is let go here: it closes itself once answered.
    end: () => {
      const mine = current
      clearTimeout(renew)
      current = null
      ended = mine ? mine.end(latest.current.chosen) : null
    },
    answer: async (recording: Blob) => {
      const { sessionId, chosen } = latest.current
      const heard = await (ended ?? Promise.resolve(null))
      ended = null

      if (heard) {
        return { ...heard, live: true }
      }

      const sent = await sendSpokenAnswer(sessionId, recording, chosen)

      return { ...sent, live: false }
    },
  }
}
