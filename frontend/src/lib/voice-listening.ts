import {
  FRAME_MS,
  IDLE_RESTART_MS,
  MAX_ANSWER_MS,
  MIN_VOICED_MS,
  SPEECH_LEVEL,
  SPEECH_PROBABILITY,
} from "@/config/voice"

export type Listener = {
  // Stops sending speech (muted, or while an answer is understood); resume starts afresh.
  pause: () => void
  resume: () => void
  stop: () => void
}

/** A voice-activity detector on the microphone (lib/voice-vad.ts): each frame's probability of
 * being speech, and where a stretch of speech starts and ends (or turns out too short). */
export type Detector = {
  start: () => Promise<void>
  pause: () => Promise<void>
  destroy: () => Promise<void>
}
export type DetectorEvents = {
  onFrame: (speech: number, samples: Float32Array) => void
  onSpeechStart: () => void
  onSpeechEnd: () => void
  onMisfire: () => void
}
export type OpenDetector = (events: DetectorEvents) => Promise<Detector>

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

/** Listens all the time once resumed, and gives each stretch of the candidate's speech alone,
 * recorded in `type`: the detector says where speech starts and ends, and a stretch counts once
 * MIN_VOICED_MS of it is speech loud enough to be theirs. A cough, a knock or thunder is no
 * speech, and silence is never sent. Time is counted in the detector's frames. Starts paused;
 * the detector loads meanwhile (its failure rejects). */
export async function listen(
  stream: MediaStream,
  type: string,
  openDetector: OpenDetector,
  handlers: {
    onSpeechStart: () => void
    // The speech and how long of it was voiced, in milliseconds.
    onSpeech: (audio: Blob, voicedMs: number) => void
  }
): Promise<Listener> {
  const format = type.split(";")[0]
  let recorder: MediaRecorder | null = null
  let chunks: Blob[] = []
  // Since the recording started, and of it, voiced; whether the detector is in a stretch of
  // speech, and whether it counts as the candidate's.
  let elapsed = 0
  let voiced = 0
  let inSpeech = false
  let heard = false
  let paused = true

  function record() {
    chunks = []
    recorder = new MediaRecorder(stream, { mimeType: type })
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunks.push(event.data)
      }
    }
    recorder.start()
    elapsed = 0
    voiced = 0
    inSpeech = false
    heard = false
  }

  // Ends the recording; `keep` gives it to onSpeech.
  function finish(keep: boolean) {
    const done = recorder
    recorder = null

    if (!done || done.state === "inactive") {
      return
    }

    const voicedMs = voiced
    done.onstop = () => {
      if (keep) {
        handlers.onSpeech(new Blob(chunks, { type: format }), voicedMs)
      }
    }
    done.stop()
  }

  // One answer at a time: listening waits for a resume after sending.
  function send() {
    finish(true)
    paused = true
    void detector.pause()
  }

  // Not the candidate speaking: dropped, and the recording starts afresh.
  function drop() {
    finish(false)
    record()
  }

  function onFrame(speech: number, samples: Float32Array) {
    if (paused || !recorder) {
      return
    }

    elapsed += FRAME_MS

    if (
      inSpeech &&
      speech >= SPEECH_PROBABILITY &&
      level(samples) >= SPEECH_LEVEL
    ) {
      voiced += FRAME_MS
    }

    if (inSpeech && !heard && voiced >= MIN_VOICED_MS) {
      heard = true
      handlers.onSpeechStart()
    }

    if (elapsed >= MAX_ANSWER_MS) {
      // As long as an answer may be: sent, or dropped when it was never the candidate.
      if (heard) {
        send()
      } else {
        drop()
      }
    } else if (!inSpeech && elapsed >= IDLE_RESTART_MS) {
      drop()
    }
  }

  function onSpeechEnd() {
    if (paused || !recorder) {
      return
    }

    if (heard) {
      send()
    } else {
      drop()
    }
  }

  const detector = await openDetector({
    onFrame,
    onSpeechStart: () => {
      inSpeech = !paused
    },
    onSpeechEnd,
    onMisfire: onSpeechEnd,
  })

  return {
    pause: () => {
      paused = true
      finish(false)
      void detector.pause()
    },
    resume: () => {
      finish(false)
      record()
      paused = false
      void detector.start()
    },
    stop: () => {
      paused = true
      finish(false)
      void detector.destroy()
    },
  }
}
