import {
  ACCOUNT_IMAGE_ORIGINS,
  FIREBASE_CONNECT_ORIGINS,
  PADDLE_ORIGINS,
  TURNSTILE_ORIGINS,
  YOUTUBE_ORIGINS,
} from "@/config/security"

/**
 * The page's Content-Security-Policy. Scripts run only with this request's nonce, or when a
 * script with it loads them ('strict-dynamic'), which covers Firebase loading Google's sign-in
 * script. Styles allow inline ones: components set style attributes and inject style tags.
 */
export function contentSecurityPolicy(
  nonce: string,
  isDev: boolean,
  // Who may show the page in a frame: no one, but a company's own site its embedded interview.
  frameAncestors = "'none'"
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
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${devScript}`,
    "style-src 'self' 'unsafe-inline'",
    `img-src 'self' blob: data: ${[...ACCOUNT_IMAGE_ORIGINS, ...PADDLE_ORIGINS].join(" ")}`,
    "font-src 'self'",
    `connect-src 'self' ${[...FIREBASE_CONNECT_ORIGINS, ...PADDLE_ORIGINS].join(" ")} ${emulator}${devConnect}`,
    `frame-src https://${authDomain} https://apis.google.com ${[...PADDLE_ORIGINS, ...TURNSTILE_ORIGINS, ...YOUTUBE_ORIGINS].join(" ")} ${emulator}`,
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    `frame-ancestors ${frameAncestors}`,
    ...(isDev ? [] : ["upgrade-insecure-requests"]),
  ]
    .map((directive) => directive.trim())
    .join("; ")
}
