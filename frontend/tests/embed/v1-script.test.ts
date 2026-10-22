// The hosted embed script (public/embed/v1.js), run in a sandbox with a fake page: what a site
// that embeds an interview relies on. The browser behaviour itself is the embed spec's
// (e2e_tests/signed-in/specs/i-api-embed.spec.ts).
import { readFileSync } from "node:fs"
import { runInNewContext } from "node:vm"

import { describe, expect, it } from "vitest"

const SCRIPT = readFileSync(
  new URL("../../public/embed/v1.js", import.meta.url),
  "utf8"
)
const ORIGIN = "https://prepza.ai"
const URL_OF_INVITE = `${ORIGIN}/invite/abc`

type Listener = (event: {
  origin: string
  source: unknown
  data: unknown
}) => void

function page(queued: object[] = []) {
  const listeners: Listener[] = []
  const timers: (() => void)[] = []
  const frames: { contentWindow: object; style: Record<string, string> }[] = []
  const elements: Record<string, object> = {
    "#interview": { appendChild: () => {} },
  }
  const window = {
    Prepza: { q: queued },
    location: { origin: "https://jobs.example.com" },
    addEventListener: (_: string, listener: Listener) =>
      listeners.push(listener),
    removeEventListener: () => {},
    setTimeout: (callback: () => void) => timers.push(callback),
    clearTimeout: () => {},
  }
  const document = {
    currentScript: { src: `${ORIGIN}/embed/v1.js` },
    querySelector: (selector: string) => elements[selector] ?? null,
    createElement: () => {
      const frame = { contentWindow: {}, style: {}, remove: () => {} }
      frames.push(frame)

      return frame
    },
  }
  runInNewContext(SCRIPT, { window, document, URL, console })

  return {
    window: window as typeof window & {
      Prepza: { embed: (o: object) => void }
    },
    listeners,
    timers,
    frames,
  }
}

describe("the embed script", () => {
  it("runs every queued call even when one throws, and still reports that one", () => {
    const { frames, timers } = page([
      { element: "#missing", url: URL_OF_INVITE },
      { element: "#interview", url: URL_OF_INVITE },
    ])

    expect(frames).toHaveLength(1)
    // The missing element's error is thrown again on its own, after the queue ran.
    const thrown = timers.map((timer) => {
      try {
        timer()
      } catch (error) {
        return (error as Error).message
      }
    })
    expect(thrown).toContain("Prepza.embed: no element #missing")
  })

  it("passes a finished candidate's id only when it is a string", () => {
    const { window, listeners, frames } = page()
    const finished: unknown[] = []
    window.Prepza.embed({
      element: "#interview",
      url: URL_OF_INVITE,
      onFinish: (value: unknown) => finished.push(value),
    })
    const message = (candidateId: unknown) =>
      listeners[0]({
        origin: ORIGIN,
        source: frames[0].contentWindow,
        data: { source: "prepza", version: 1, type: "finished", candidateId },
      })

    message("cand-1")
    message({ toString: "evil" })

    expect(finished).toEqual([
      { candidateId: "cand-1" },
      { candidateId: undefined },
    ])
  })

  it("is written in ES5, so every browser a site supports can run it", () => {
    const code = SCRIPT.replace(/\/\*[\s\S]*?\*\//g, "").replace(
      /\/\/.*$/gm,
      ""
    )

    expect(code).not.toMatch(
      /=>|\blet\b|\bconst\b|`|\bclass\b|\.\.\.|\basync\b|\bawait\b/
    )
  })
})
