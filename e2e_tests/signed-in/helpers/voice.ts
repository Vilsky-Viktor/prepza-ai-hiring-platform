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

/** A fake microphone in `page`: getUserMedia gives a silent tone that `say` turns up for a
 * moment, as a candidate speaking; with `deny`, the browser refuses it, as a candidate blocking
 * it would. */
export async function fakeMicrophone(page: Page) {
  await page.addInitScript(() => {
    const fake = window as unknown as {
      micDenied: boolean
      sayFor: (ms: number) => void
    }
    let gain: GainNode | null = null
    fake.micDenied = false
    fake.sayFor = (ms) => {
      gain!.gain.value = 0.5
      window.setTimeout(() => {
        gain!.gain.value = 0
      }, ms)
    }
    navigator.mediaDevices.getUserMedia = async () => {
      if (fake.micDenied) {
        throw new DOMException("Permission denied", "NotAllowedError")
      }

      const context = new AudioContext()
      const tone = context.createOscillator()
      gain = context.createGain()
      gain.gain.value = 0
      const out = context.createMediaStreamDestination()
      tone.connect(gain).connect(out)
      tone.start()
      await context.resume()

      return out.stream
    }
  })

  return {
    deny: (denied: boolean) =>
      page.evaluate((value) => {
        ;(window as unknown as { micDenied: boolean }).micDenied = value
      }, denied),
    // A second of speech: long enough to be words, so Mira says "Got it."
    say: () =>
      page.evaluate(() =>
        (window as unknown as { sayFor: (ms: number) => void }).sayFor(1000)
      ),
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
