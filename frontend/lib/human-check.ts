import { HUMAN_CHECK_HEADER, TURNSTILE_SCRIPT } from "@/constants/security"

// Cloudflare Turnstile's own interface, as much of it as this uses.
type Turnstile = {
  render: (container: HTMLElement, options: Record<string, unknown>) => string
  execute: (widget: string) => void
  reset: (widget: string) => void
}

declare global {
  interface Window {
    turnstile?: Turnstile
  }
}

const SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ?? ""

let loading: Promise<Turnstile | null> | null = null
let widget: string | null = null
let waiting: ((token: string) => void) | null = null

/** Turnstile's script, once; null when it can't load (a blocker): the service then refuses,
 * and its message says what to do. */
function load(): Promise<Turnstile | null> {
  if (window.turnstile) {
    return Promise.resolve(window.turnstile)
  }

  loading ??= new Promise((resolve) => {
    const script = document.createElement("script")
    script.src = TURNSTILE_SCRIPT
    script.async = true
    script.onload = () => resolve(window.turnstile ?? null)
    script.onerror = () => {
      loading = null
      resolve(null)
    }
    document.head.appendChild(script)
  })

  return loading
}

function answer(token: string) {
  waiting?.(token)
  waiting = null
}

/** The invisible widget, once, at the bottom of the screen: rendered without running the
 * check, which `humanToken` starts. */
function widgetOf(turnstile: Turnstile) {
  if (widget === null) {
    const box = document.createElement("div")
    box.className = "fixed bottom-4 left-1/2 z-50 -translate-x-1/2"
    document.body.appendChild(box)
    widget = turnstile.render(box, {
      sitekey: SITE_KEY,
      appearance: "interaction-only",
      execution: "execute",
      callback: answer,
      "error-callback": () => answer(""),
      "expired-callback": () => answer(""),
    })
  }

  return widget
}

/** Turnstile ready for a form that will ask for a token: its script loaded and its widget
 * rendered when the form appears, so a click only runs the check (hooks/use-human-check.ts). */
export async function prepareHumanCheck() {
  const turnstile = SITE_KEY ? await load() : null

  if (turnstile) {
    widgetOf(turnstile)
  }
}

/** A one-time token saying a person is here, for a request the service checks ("" without the
 * check set up, or when it can't run). Most people see nothing; the few Cloudflare isn't sure
 * about get a small challenge at the bottom of the screen. */
export async function humanToken(): Promise<string> {
  const turnstile = SITE_KEY ? await load() : null

  if (!turnstile) {
    return ""
  }

  return new Promise((resolve) => {
    answer("")
    waiting = resolve
    // A widget rendered before (by its form, or for an earlier check) starts over.
    const rendered = widget !== null
    const id = widgetOf(turnstile)

    if (rendered) {
      turnstile.reset(id)
    }

    turnstile.execute(id)
  })
}

/** The header a checked request sends (none when `needed` is false). */
export async function humanHeaders(
  needed = true
): Promise<Record<string, string>> {
  return needed ? { [HUMAN_CHECK_HEADER]: await humanToken() } : {}
}
