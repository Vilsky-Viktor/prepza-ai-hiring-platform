// Tests voice mode's listening in the browser (frontend/src/lib/voice-listening.ts) offline: each
// of datasets/voice_sounds.json's sounds (a cough, a knock, thunder: no speech) and
// voice_answers.json's spoken answers is decoded to 16 kHz (as the detector hears it), padded with
// silence, and fed frame by frame through the site's own listener with the site's own detector:
// Silero VAD's model and vad-web's frame logic on ONNX Runtime, with config/voice.ts's options.
// Code grades it: a sound must never start a recording or be sent, an answer must be sent, a
// short one ("B", "yes") above all. Not covered: the browser's own noise suppression and
// automatic gain, which run before the detector there.
//
//   node --import ./evals/scripts/frontend_alias.mjs evals/scripts/voice_listening_test.mjs [label]
//
// Runs on the host with the frontend's packages and ffmpeg; free (no model calls).
import { execFileSync } from "node:child_process"
import { createHash } from "node:crypto"
import { mkdirSync, readFileSync, writeFileSync } from "node:fs"
import { createRequire } from "node:module"

import { FRAME_MS, MAX_ANSWER_MS, VAD_OPTIONS } from "@/config/voice"
import { listen } from "@/lib/voice-listening"

const EVALS = new URL("../", import.meta.url)
const DATASETS = new URL("datasets/", EVALS)
const CONFIG = new URL("../frontend/src/config/voice.ts", EVALS)
const require = createRequire(new URL("../frontend/package.json", EVALS))
const ort = require("onnxruntime-web")
const { FrameProcessor, Message } = require("@ricky0123/vad-web")
const { Silero } = require("@ricky0123/vad-web/dist/models")
const MODEL = require.resolve("@ricky0123/vad-web/dist/silero_vad_v5.onnx")
const RATE = 16_000
const FRAME = 512
// Silence around each clip, in seconds: the speech ends only after a silence.
const BEFORE = 0.5
const AFTER = 1.5
// A short answer: a word or two.
const SHORT_WORDS = 2

ort.env.wasm.numThreads = 1
ort.env.logLevel = "error"

class FakeRecorder {
  state = "inactive"
  start() {
    this.state = "recording"
  }
  stop() {
    this.state = "inactive"
    this.ondataavailable?.({ data: new Blob(["sound"]) })
    this.onstop?.()
  }
}

globalThis.MediaRecorder = FakeRecorder

function decode(path) {
  const raw = execFileSync(
    "ffmpeg",
    ["-loglevel", "error", "-i", path, "-ac", "1", "-ar", String(RATE), "-f", "f32le", "-"],
    { maxBuffer: 1 << 28 }
  )
  const audio = new Float32Array(raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.length))
  const padded = new Float32Array(Math.ceil((BEFORE + AFTER) * RATE) + audio.length)
  padded.set(audio, BEFORE * RATE)

  return padded
}

/** The site's detector, fed from `audio` instead of a microphone: the same model and frame
 * logic MicVAD runs (lib/voice-vad.ts). Its start reads the whole clip; `read` is that reading. */
async function fileDetector(audio) {
  const model = await Silero.new(ort, async () => readFileSync(MODEL).buffer)
  const found = { read: Promise.resolve() }

  found.open = async (events) => {
    const processor = new FrameProcessor(model.process, model.reset_state, VAD_OPTIONS, FRAME_MS)
    const handle = (event) => {
      if (event.msg === Message.FrameProcessed) {
        events.onFrame(event.probs.isSpeech, event.frame)
      } else if (event.msg === Message.SpeechStart) {
        events.onSpeechStart()
      } else if (event.msg === Message.SpeechEnd) {
        events.onSpeechEnd()
      } else if (event.msg === Message.VADMisfire) {
        events.onMisfire()
      }
    }

    return {
      start: async () => {
        processor.resume()
        found.read = (async () => {
          for (let at = 0; at + FRAME <= audio.length; at += FRAME) {
            await processor.process(audio.slice(at, at + FRAME), handle)
          }
        })()
      },
      pause: async () => processor.pause(handle),
      destroy: async () => model.release(),
    }
  }

  return found
}

/** What the listener did with one clip: whether it took it for the candidate speaking, and sent
 * it. */
async function heard(path) {
  const audio = decode(path)
  let started = false
  let sent = false
  const detector = await fileDetector(audio)
  const listener = await listen({}, "audio/webm", detector.open, {
    onSpeechStart: () => {
      started = true
    },
    onSpeech: () => {
      sent = true
    },
  })
  // Resuming starts the detector, which here reads the whole clip.
  listener.resume()
  await detector.read
  listener.stop()

  return { started, sent, seconds: audio.length / RATE }
}

function wilson(hits, total) {
  if (!total) {
    return "n/a"
  }

  const z = 1.96
  const p = hits / total
  const centre = (p + (z * z) / (2 * total)) / (1 + (z * z) / total)
  const margin =
    (z * Math.sqrt((p * (1 - p)) / total + (z * z) / (4 * total * total))) / (1 + (z * z) / total)
  const percent = (value) => (100 * value).toFixed(1)

  return `${percent(p)}% (${percent(Math.max(0, centre - margin))}-${percent(Math.min(1, centre + margin))})`
}

const share = (rows, key) => wilson(rows.filter((row) => row[key]).length, rows.length)
const load = (name) => JSON.parse(readFileSync(new URL(name, DATASETS), "utf8"))
const rows = []

for (const sound of load("voice_sounds.json").items) {
  const path = new URL(`audio/sound_${sound.id}.ogg`, DATASETS).pathname
  rows.push({ id: sound.id, kind: sound.kind, speech: false, ...(await heard(path)) })
}

for (const answer of load("voice_answers.json").items.filter((item) => item.spoken)) {
  const path = new URL(`audio/answer_${answer.id}.ogg`, DATASETS).pathname
  const short = answer.said.split(/\s+/).length <= SHORT_WORDS
  rows.push({ id: answer.id, kind: answer.kind, speech: true, short, ...(await heard(path)) })
}

const sounds = rows.filter((row) => !row.speech)
const answers = rows.filter((row) => row.speech)
const scores = {
  sounds_started: share(sounds, "started"),
  sounds_sent: share(sounds, "sent"),
  answers_sent: share(answers, "sent"),
  short_answers_sent: share(
    answers.filter((row) => row.short),
    "sent"
  ),
}
const commit = execFileSync("git", ["rev-parse", "--short", "HEAD"]).toString().trim()
const changed = execFileSync("git", ["status", "--porcelain", "--", "frontend/src", "evals"], {
  cwd: new URL("../", EVALS),
})
const run = {
  date: new Date().toISOString().slice(0, 10),
  commit: changed.length ? `${commit}+changes` : commit,
  constants: createHash("sha256").update(readFileSync(CONFIG)).digest("hex").slice(0, 10),
  model: "Silero VAD v5 (vad-web, onnxruntime-web)",
  max_answer_ms: MAX_ANSWER_MS,
  scores,
  cost: 0,
}
const label = process.argv[2] ?? "run"
mkdirSync(new URL("results/", EVALS), { recursive: true })
writeFileSync(
  new URL(`results/voice_listening_${label}.json`, EVALS),
  `${JSON.stringify({ run, rows }, null, 1)}\n`
)
console.log(JSON.stringify(scores, null, 1))

for (const row of rows) {
  if (row.speech !== row.sent) {
    console.log(`- ${row.speech ? "missed" : "SENT"} ${row.id} [${row.kind}]`)
  }
}
