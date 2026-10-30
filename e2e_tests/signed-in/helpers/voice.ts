import { readFileSync } from "node:fs"

import { expect, type Page, type Route } from "@playwright/test"

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
export type Understood = { heard: string; intent: string; picks: number[] }

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

/** Mira's side mocked at the network edge on `page`: every clip she says (the question, her
 * phrases, a confirmation) is a moment of silence, reading ahead does nothing, and each spoken
 * answer waits for the test to `answer` it with what the service understood. `asked` lists the
 * voice requests made, as paths with their queries. */
export async function fakeMira(page: Page) {
  const asked: string[] = []
  const waiting: { route: Route; url: URL }[] = []

  await page.route("**/api/rounds/sessions/*/voice/**", async (route) => {
    const url = new URL(route.request().url())
    const path = url.pathname.replace(/^.*\/voice\//, "") + url.search
    asked.push(path)

    if (path.startsWith("answers")) {
      waiting.push({ route, url })

      return
    }

    if (path.startsWith("next-question")) {
      await route.fulfill({ status: 204 })

      return
    }

    await route.fulfill({ body: CLIP, contentType: "audio/wav" })
  })

  return {
    asked,
    /** The spoken answer waiting, once sent: the choice on screen it carried (`waiting`). */
    sent: async () => {
      await expectSoon(() => waiting.length > 0)

      return waiting[0].url.searchParams.getAll("waiting").map(Number)
    },
    /** Answers the spoken answer waiting with what the service understood. */
    answer: async (understood: Understood) => {
      await expectSoon(() => waiting.length > 0)
      const { route } = waiting.shift()!
      await route.fulfill({ json: understood })
    },
  }
}

/** Polls `ready` until it holds. */
async function expectSoon(ready: () => boolean) {
  await expect.poll(ready).toBe(true)
}

/** Keeps OpenAI out of a voice interview's server side: the company's daily count of questions
 * read aloud for the first time is set past any limit, so rounds refuses to read a question when
 * it opens and the question goes on unread (its clips are mocked in the browser). The key is
 * rounds' (services/voice_limits.py), the company's own, so no other test is touched. */
export async function noReadingAloud(companyId: string) {
  await redis("SET", `rate:voice:clips:company:${companyId}`, "1000000000", "EX", "86400")
}
