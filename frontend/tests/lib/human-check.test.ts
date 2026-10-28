import { beforeEach, describe, expect, it, vi } from "vitest"

// Turnstile's script and widget in a stand-in page: the script "loads" as soon as it's added,
// and the widget answers each check with a token.
function fakePage() {
  const added: { src?: string; onload?: () => void }[] = []
  const turnstile = {
    render: vi.fn(
      (_box: unknown, options: { callback: (token: string) => void }) => {
        turnstile.answer = options.callback

        return "widget-1"
      }
    ),
    execute: vi.fn(() => turnstile.answer("token")),
    reset: vi.fn(),
    answer: (() => {}) as (token: string) => void,
  }
  const window: { turnstile?: object } = {}
  const element = () => ({ className: "" })

  vi.stubGlobal("window", window)
  vi.stubGlobal("document", {
    createElement: (tag: string) => (tag === "script" ? {} : element()),
    head: {
      appendChild: (script: { src?: string; onload?: () => void }) => {
        added.push(script)
        window.turnstile = turnstile
        script.onload?.()
      },
    },
    body: { appendChild: vi.fn() },
  })

  return { added, turnstile }
}

// A fresh module each time: it keeps its script and widget between calls.
async function humanCheck() {
  vi.resetModules()

  return import("@/lib/human-check")
}

describe("human check", () => {
  beforeEach(() => {
    vi.stubEnv("NEXT_PUBLIC_TURNSTILE_SITE_KEY", "site-key")
  })

  it("loads the script and renders the widget when its form appears, without a check", async () => {
    const { added, turnstile } = fakePage()
    const { prepareHumanCheck } = await humanCheck()

    await prepareHumanCheck()

    expect(added).toHaveLength(1)
    expect(added[0].src).toContain("render=explicit")
    expect(turnstile.render).toHaveBeenCalledTimes(1)
    expect(turnstile.execute).not.toHaveBeenCalled()
  })

  it("only runs the check on sending, with the widget the form rendered", async () => {
    const { added, turnstile } = fakePage()
    const { humanHeaders, prepareHumanCheck } = await humanCheck()

    await prepareHumanCheck()
    const headers = await humanHeaders()

    expect(headers).toEqual({ "X-Human-Check": "token" })
    expect(added).toHaveLength(1)
    expect(turnstile.render).toHaveBeenCalledTimes(1)
    expect(turnstile.execute).toHaveBeenCalledWith("widget-1")
  })

  it("still renders the widget for a request sent before any form prepared it", async () => {
    const { turnstile } = fakePage()
    const { humanToken } = await humanCheck()

    expect(await humanToken()).toBe("token")
    expect(turnstile.render).toHaveBeenCalledTimes(1)
    expect(turnstile.reset).not.toHaveBeenCalled()
  })

  it("leaves Turnstile out without a site key", async () => {
    vi.stubEnv("NEXT_PUBLIC_TURNSTILE_SITE_KEY", "")
    const { added } = fakePage()
    const { humanToken, prepareHumanCheck } = await humanCheck()

    await prepareHumanCheck()

    expect(await humanToken()).toBe("")
    expect(added).toHaveLength(0)
  })

  it("loads the script when an element on the page is named turnstile", async () => {
    const { added, turnstile } = fakePage()
    ;(globalThis.window as { turnstile?: object }).turnstile = { nodeType: 1 }
    const { prepareHumanCheck } = await humanCheck()

    await prepareHumanCheck()

    expect(added).toHaveLength(1)
    expect(turnstile.render).toHaveBeenCalledTimes(1)
  })
})
