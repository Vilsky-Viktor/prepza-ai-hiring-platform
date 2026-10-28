// Google services that Firebase sign-in (signInWithPopup) talks to.
export const FIREBASE_CONNECT_ORIGINS = [
  "https://identitytoolkit.googleapis.com",
  "https://securetoken.googleapis.com",
  "https://www.googleapis.com",
  "https://apis.google.com",
  // Google's sign-in scripts check the connection by fetching an image from here.
  "https://www.google.com",
]

// Paddle's checkout runs in a frame from these, and Paddle.js talks to them.
export const PADDLE_ORIGINS = ["https://*.paddle.com"]

// YouTube's no-cookie player, in the home page's video window.
export const YOUTUBE_ORIGINS = ["https://www.youtube-nocookie.com"]

// Profile photos of Google accounts.
export const ACCOUNT_IMAGE_ORIGINS = ["https://*.googleusercontent.com"]

// Sentry: share of page loads and requests traced for performance.
export const SENTRY_TRACES_SAMPLE_RATE = 0.1

// Cloudflare Turnstile, the "I'm not a robot" check (lib/human-check.ts): its script, and its
// frame, which shows a challenge to the few people it isn't sure about.
export const TURNSTILE_SCRIPT =
  "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit"
export const TURNSTILE_ORIGINS = ["https://challenges.cloudflare.com"]
// The header a request carries its token in (services check it: prepza_common human_check).
export const HUMAN_CHECK_HEADER = "X-Human-Check"
