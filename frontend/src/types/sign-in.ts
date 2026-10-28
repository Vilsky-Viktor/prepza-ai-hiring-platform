import type { SIGN_IN_PROVIDERS } from "@/config/auth"

export type SignInProvider = (typeof SIGN_IN_PROVIDERS)[number]

/** How a sign-in attempt ended. `link`: the email has an account under another way of signing
 * in; signing in that way links this one to it. `verify`: signed in, but the email isn't
 * verified yet, and a link to verify it was sent. */
export type SignInResult =
  "done" | "verify" | "verifyFailed" | "cancelled" | "link" | "failed"
