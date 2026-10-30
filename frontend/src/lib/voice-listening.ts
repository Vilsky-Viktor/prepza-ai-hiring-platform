import {
  IDLE_RESTART_MS,
  LEVEL_EVERY_MS,
  MAX_ANSWER_MS,
  SPEECH_END_MS,
  SPEECH_LEVEL,
  SPEECH_START_MS,
} from "@/config/voice"

export type Listener = {
  // Stops sending speech (muted, or while an answer is understood); resume starts afresh.
  pause: () => void
  resume: () => void
  stop: () => void
}

/** The microphone, opened once for the whole interview with the browser's voice processing (echo
 * cancellation, noise suppression, automatic gain). Throws the browser's error when it isn't
 * allowed. */
export function openMicrophone(): Promise<MediaStream> {
  return navigator.mediaDevices.getUserMedia({
    audio: {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  })
}

/** The level of the sound now: its root mean square, 0 to 1. */
export function level(samples: Float32Array) {
  let sum = 0

  for (const sample of samples) {
    sum += sample * sample
  }

  return Math.sqrt(sum / samples.length)
}

/** Listens all the time: notices when someone starts and stops speaking (from the microphone's
 * level) and gives that stretch alone, recorded in `type`; silence is never sent. */
export function listen(
  context: AudioContext,
  stream: MediaStream,
  type: string,
  handlers: {
    onSpeechStart: () => void
    // The speech and how long it was voiced (above the speech level), in milliseconds.
    onSpeech: (audio: Blob, voicedMs: number) => void
  }
): Listener {
  const analyser = context.createAnalyser()
  analyser.fftSize = 1024
  context.createMediaStreamSource(stream).connect(analyser)
  const samples = new Float32Array(analyser.fftSize)
  const format = type.split(";")[0]
  let recorder: MediaRecorder | null = null
  let chunks: Blob[] = []
  let recordingSince = 0
  let above = 0
  let below = 0
  let speaking = false
  let voiced = 0
  let paused = false

  function record() {
    chunks = []
    recorder = new MediaRecorder(stream, { mimeType: type })
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunks.push(event.data)
      }
    }
    recorder.start()
    recordingSince = Date.now()
    above = 0
    below = 0
    speaking = false
    voiced = 0
  }

  // Ends the recording; `keep` gives it to onSpeech.
  function finish(keep: boolean) {
    const done = recorder
    recorder = null

    if (!done || done.state === "inactive") {
      return
    }

    done.onstop = () => {
      if (keep) {
        handlers.onSpeech(new Blob(chunks, { type: format }), voiced)
      }
    }
    done.stop()
  }

  function tick() {
    if (paused || !recorder) {
      return
    }

    analyser.getFloatTimeDomainData(samples)
    const threshold = SPEECH_LEVEL
    const now = level(samples)

    if (!speaking) {
      above = now > threshold ? above + LEVEL_EVERY_MS : 0

      if (above >= SPEECH_START_MS) {
        speaking = true
        voiced = above
        handlers.onSpeechStart()
      } else if (Date.now() - recordingSince > IDLE_RESTART_MS) {
        // Silence so far: dropped, and the recording starts again.
        finish(false)
        record()
      }

      return
    }

    below = now < threshold * 0.6 ? below + LEVEL_EVERY_MS : 0
    voiced += now > threshold ? LEVEL_EVERY_MS : 0

    if (below >= SPEECH_END_MS || Date.now() - recordingSince > MAX_ANSWER_MS) {
      finish(true)
      paused = true
    }
  }

  const timer = window.setInterval(tick, LEVEL_EVERY_MS)
  record()

  return {
    pause: () => {
      paused = true
      finish(false)
    },
    resume: () => {
      paused = false
      finish(false)
      record()
    },
    stop: () => {
      window.clearInterval(timer)
      finish(false)
      analyser.disconnect()
    },
  }
}
