import { readFileSync } from "node:fs"

import { expect, type Page, type WebSocketRoute } from "@playwright/test"

import { redis } from "./redis"

// A short moment of silence as a WAV file: every clip Mira says, mocked at the network edge.
const CLIP = (() => {
  const samples = 800
  const wav = Buffer.alloc(44 + samples)
  wav.write("RIFF", 0)
  wav.writeUInt32LE(36 + samples, 4)
  wav.write("WAVEfmt ", 8)
  wav.writeUInt32LE(16, 16)
  wav.writeUInt16LE(1, 20)
  wav.writeUInt16LE(1, 22)
  wav.writeUInt32LE(8000, 24)
  wav.writeUInt32LE(8000, 28)
  wav.writeUInt16LE(1, 32)
  wav.writeUInt16LE(8, 34)
  wav.write("data", 36)
  wav.writeUInt32LE(samples, 40)
  wav.fill(128, 44)

  return wav
})()

// What the service understood from a spoken answer (rounds' VoiceAnswerOut).
export type Understood = { heard: string; intent: string; picks: number[]; clear?: boolean }

// A sentence of made-up speech (the evals' voice message v01, spoken by a speech model): the fake
// microphone's voice. Voice mode listens for speech only, so a tone wouldn't do.
const SPEECH = readFileSync(new URL("../media/speech.ogg", import.meta.url)).toString("base64")

/** A fake microphone in `page`: getUserMedia gives silence that `say` fills with a spoken
 * sentence, after a cough first when asked; with `deny`, the browser refuses it, as a candidate
 * blocking it would. `sentDuring` lists, for each spoken answer sent, what the microphone was
 * playing when it went: a cough sent would show "cough". */
export async function fakeMicrophone(page: Page) {
  await page.addInitScript((speech) => {
    const fake = window as unknown as {
      micDenied: boolean
      playing: string
      sentDuring: string[]
      play: (cough: boolean) => Promise<void>
    }
    let context: AudioContext | null = null
    let out: MediaStreamAudioDestinationNode | null = null
    fake.micDenied = false
    fake.playing = "nothing"
    fake.sentDuring = []
    const send = window.fetch.bind(window)
    window.fetch = (input, init) => {
      if (String(input instanceof Request ? input.url : input).includes("/voice/answers")) {
        fake.sentDuring.push(fake.playing)
      }

      return send(input, init)
    }

    // Plays `buffer` into the microphone to its end.
    function play(buffer: AudioBuffer) {
      const source = context!.createBufferSource()
      source.buffer = buffer
      source.connect(out!)

      return new Promise<void>((done) => {
        source.onended = () => done()
        source.start()
      })
    }

    // Two coughs: bursts of noise, loud and short, then a second of silence.
    function cough() {
      const rate = context!.sampleRate
      const buffer = context!.createBuffer(1, rate * 1.6, rate)
      const samples = buffer.getChannelData(0)

      for (let i = 0; i < rate * 0.6; i++) {
        const t = (i / rate) % 0.3
        samples[i] = (Math.random() * 2 - 1) * 0.8 * Math.exp(-t * 12)
      }

      return buffer
    }

    fake.play = async (coughFirst) => {
      if (coughFirst) {
        fake.playing = "cough"
        await play(cough())
      }

      const bytes = Uint8Array.from(atob(speech), (c) => c.charCodeAt(0))
      fake.playing = "speech"
      await play(await context!.decodeAudioData(bytes.buffer))
      fake.playing = "nothing"
    }
    navigator.mediaDevices.getUserMedia = async () => {
      if (fake.micDenied) {
        throw new DOMException("Permission denied", "NotAllowedError")
      }

      context = new AudioContext()
      out = context.createMediaStreamDestination()
      await context.resume()

      return out.stream
    }
  }, SPEECH)

  return {
    deny: (denied: boolean) =>
      page.evaluate((value) => {
        ;(window as unknown as { micDenied: boolean }).micDenied = value
      }, denied),
    // A sentence spoken (and a cough before it, with `cough`): long enough for "Got it."
    say: (cough = false) =>
      page.evaluate((first) => {
        void (window as unknown as { play: (cough: boolean) => Promise<void> }).play(first)
      }, cough),
    sentDuring: () =>
      page.evaluate(() => (window as unknown as { sentDuring: string[] }).sentDuring),
  }
}

// A spoken answer waiting for the test's `answer`: the choice on screen it carried, and how it's
// answered (the upload's response, or the live stream's message).
type Waiting = { waiting: number[]; reply: (understood: Understood) => Promise<void> }
// A live stream (lib/voice-live.ts) the page opened: its audio's bytes so far.
type Stream = { socket: WebSocketRoute; started: boolean; ended: boolean; audio: number }

/** Mira's side mocked at the network edge on `page`: every clip she says (the question, her
 * phrases, a confirmation) is a moment of silence, reading ahead does nothing, and each spoken
 * answer waits for the test to `answer` it with what the service understood. Live listening's
 * stream is refused, so answers are uploaded as recordings, unless `live`: then it's ready at
 * once, and an answer streamed to its end waits the same way (`dropStream` cuts the one being
 * spoken, so the page uploads the recording instead). `asked` lists the voice requests made, as
 * paths with their queries (her short clips are fetched ahead, said or not); `said` lists the
 * clips she played, the same way. */
export async function fakeMira(page: Page, live = false) {
  const asked: string[] = []
  const waiting: Waiting[] = []
  const streams: Stream[] = []

  // Each clip's address is traced back to the path it was fetched from, and each play recorded.
  await page.addInitScript(() => {
    const page = window as unknown as { miraSaid: string[] }
    page.miraSaid = []
    const paths = new Map<string, string>()
    const blob = Response.prototype.blob
    Response.prototype.blob = async function () {
      const found = await blob.call(this)
      const url = new URL(this.url, location.href)

      if (url.pathname.includes("/voice/")) {
        const path = url.pathname.replace(/^.*\/voice\//, "") + url.search
        ;(found as Blob & { voicePath?: string }).voicePath = path
      }

      return found
    }
    const create = URL.createObjectURL.bind(URL)
    URL.createObjectURL = (object: Blob | MediaSource) => {
      const address = create(object)
      const path = (object as Blob & { voicePath?: string }).voicePath

      if (path) {
        paths.set(address, path)
      }

      return address
    }
    const play = HTMLMediaElement.prototype.play
    HTMLMediaElement.prototype.play = function () {
      const path = paths.get(this.src)

      if (path) {
        page.miraSaid.push(path)
      }

      return play.call(this)
    }
  })

  await page.route("**/api/rounds/sessions/*/voice/**", async (route) => {
    const url = new URL(route.request().url())
    const path = url.pathname.replace(/^.*\/voice\//, "") + url.search
    asked.push(path)

    if (path.startsWith("answers")) {
      waiting.push({
        waiting: url.searchParams.getAll("waiting").map(Number),
        reply: (understood) => route.fulfill({ json: understood }),
      })

      return
    }

    if (path.startsWith("next-question")) {
      await route.fulfill({ status: 204 })

      return
    }

    await route.fulfill({ body: CLIP, contentType: "audio/wav" })
  })

  await page.routeWebSocket(/\/voice\/stream$/, (socket) => {
    if (!live) {
      socket.close({ code: 4503 })

      return
    }

    const stream: Stream = { socket, started: false, ended: false, audio: 0 }
    streams.push(stream)
    socket.onMessage((message) => {
      if (typeof message !== "string") {
        stream.audio += message.length

        return
      }

      const step = JSON.parse(message)

      if ("token" in step) {
        socket.send(JSON.stringify({ type: "ready" }))
      } else if (step.type === "start") {
        stream.started = true
      } else if (step.type === "end") {
        stream.ended = true
        waiting.push({
          waiting: step.waiting,
          reply: async (understood) => {
            socket.send(JSON.stringify({ type: "answer", answer: understood, stages: {} }))
            await socket.close()
          },
        })
      }
    })
  })

  return {
    asked,
    said: () => page.evaluate(() => (window as unknown as { miraSaid: string[] }).miraSaid),
    /** The spoken answer waiting, once sent: the choice on screen it carried (`waiting`). */
    sent: async () => {
      await expectSoon(() => waiting.length > 0)

      return waiting[0].waiting
    },
    /** Answers the spoken answer waiting with what the service understood. */
    answer: async (understood: Understood) => {
      await expectSoon(() => waiting.length > 0)
      await waiting.shift()!.reply(understood)
    },
    /** The bytes of audio each live stream got, oldest first. */
    streamed: () => streams.map((stream) => stream.audio),
    /** Cuts the live stream carrying speech not yet ended, once some of it has arrived. */
    dropStream: async () => {
      const speaking = (stream: Stream) => stream.started && !stream.ended && stream.audio > 0
      await expectSoon(() => streams.some(speaking))
      await streams.find(speaking)!.socket.close({ code: 4502 })
    },
  }
}

/** Polls `ready` until it holds. */
async function expectSoon(ready: () => boolean) {
  await expect.poll(ready).toBe(true)
}

/** Keeps OpenAI out of a voice interview's server side: the company's daily count of questions
 * read aloud for the first time is set past any limit, so rounds refuses to read a question and
 * the question goes on unread (its clips are mocked in the browser). The key is
 * rounds' (services/voice_limits.py), the company's own, so no other test is touched. */
export async function noReadingAloud(companyId: string) {
  await redis("SET", `rate:voice:clips:company:${companyId}`, "1000000000", "EX", "86400")
}
