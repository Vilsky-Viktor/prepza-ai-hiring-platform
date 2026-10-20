// The interview a company's own site embeds in a frame (public/embed/v1.js makes the frame): its
// page, with the invite's token after it, in any language.
export const EMBED_PAGE = /^(?:\/[a-z]{2,3})?\/embedded\/([^/]+)$/

// Every message the frame sends the company's page says it's from prepza, and which version of
// the messages it speaks (the script's major version); the script listens for these kinds.
export const EMBED_SOURCE = "prepza"
export const EMBED_VERSION = 1
export const EMBED_EVENTS = {
  ready: "ready",
  started: "started",
  finished: "finished",
  resize: "resize",
  error: "error",
} as const
// Why the interview can't show, as the script's onError tells the company's page: the link is
// gone (expired, revoked or unknown), or it couldn't be read (worth trying again).
export const EMBED_ERRORS = {
  missing: "invite_unavailable",
  failed: "load_failed",
} as const

// The hosted script's headers (next.config.ts): browsers keep it 5 minutes and then use it while
// they fetch it again for a day, so a fix reaches every site soon without slowing a visit; any
// site may load it with `crossorigin`, which shows its errors there instead of "Script error.".
export const EMBED_SCRIPT_HEADERS = [
  {
    key: "Cache-Control",
    value: "public, max-age=300, stale-while-revalidate=86400",
  },
  { key: "Access-Control-Allow-Origin", value: "*" },
]

// How long the page waits for the company's domain before refusing to be framed.
export const EMBED_LOOKUP_TIMEOUT_MS = 3000
