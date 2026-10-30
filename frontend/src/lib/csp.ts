import {
  ACCOUNT_IMAGE_ORIGINS,
  FIREBASE_CONNECT_ORIGINS,
  PADDLE_ORIGINS,
  TURNSTILE_ORIGINS,
  YOUTUBE_ORIGINS,
} from "@/config/security"

/** A fresh nonce for one page: 128 random bits (CSP3 asks for at least that), base64. */
export function newNonce() {
  return btoa(
    String.fromCharCode(...crypto.getRandomValues(new Uint8Array(16)))
  )
}

// A host as a request names it: a name or address and maybe a port, nothing that could end the
// policy's directive.
const HOST = /^[a-z0-9.-]+(:\d+)?$/i

/** The site's own address for WebSockets (voice mode's live listening, lib/voice-live.ts), from
 * the request's host (with its port: the local gateway forwards it apart) and scheme: `'self'`
 * doesn't cover WebSockets in every browser. Empty for a host that isn't one. */
export function ownSocketOrigin(headers: Headers) {
  const host = headers.get("x-forwarded-host") ?? headers.get("host") ?? ""
  const scheme = headers.get("x-forwarded-proto") === "http" ? "ws" : "wss"

  return HOST.test(host) ? `${scheme}://${host}` : ""
}

/**
 * The page's Content-Security-Policy. Scripts run only with this request's nonce, or when a
 * script with it loads them ('strict-dynamic'), which covers Firebase loading Google's sign-in
 * script. Styles allow inline ones: components set style attributes and inject style tags.
 */
export function contentSecurityPolicy(
  nonce: string,
  isDev: boolean,
  // Who may show the page in a frame: no one, but a company's own site its embedded interview.
  frameAncestors = "'none'",
  // The site's own WebSocket address (ownSocketOrigin).
  socketOrigin = ""
) {
  const authDomain = process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
  const emulatorUrl = process.env.NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL
  // Locally, on whichever host the site was opened from (lib/firebase.ts).
  const emulator = emulatorUrl
    ? `${new URL(emulatorUrl).protocol}//*:${new URL(emulatorUrl).port}`
    : ""
  // React needs eval in development only, and the dev server reloads through a websocket.
  const devScript = isDev ? " 'unsafe-eval'" : ""
  const devConnect = isDev ? " ws:" : ""

  return [
    "default-src 'self'",
    // WebAssembly may compile: voice mode's speech detector runs on it (lib/voice-vad.ts).
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic' 'wasm-unsafe-eval'${devScript}`,
    "style-src 'self' 'unsafe-inline'",
    `img-src 'self' blob: data: ${[...ACCOUNT_IMAGE_ORIGINS, ...PADDLE_ORIGINS].join(" ")}`,
    "font-src 'self'",
    // Voice mode plays Mira's clips from blob addresses (fetched with the candidate's token).
    "media-src 'self' blob:",
    `connect-src 'self' ${socketOrigin} ${[...FIREBASE_CONNECT_ORIGINS, ...PADDLE_ORIGINS].join(" ")} ${emulator}${devConnect}`,
    `frame-src https://${authDomain} https://apis.google.com ${[...PADDLE_ORIGINS, ...TURNSTILE_ORIGINS, ...YOUTUBE_ORIGINS].join(" ")} ${emulator}`,
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    `frame-ancestors ${frameAncestors}`,
    // Not on the local stack (the sign-in emulator, never set in production), served over plain
    // http: Safari would upgrade the site's own files to https there, which nothing serves.
    ...(isDev || emulator ? [] : ["upgrade-insecure-requests"]),
  ]
    .map((directive) => directive.trim())
    .join("; ")
}
