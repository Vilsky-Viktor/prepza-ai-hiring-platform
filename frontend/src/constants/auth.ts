export const TOKEN_COOKIE = "prepza_token"

export const TOKEN_COOKIE_MAX_AGE = 60 * 60

export const POPUP_CLOSED_CODES = [
  "auth/popup-closed-by-user",
  "auth/cancelled-popup-request",
]

// The ways to sign in, in the order the dialog shows them.
export const SIGN_IN_PROVIDERS = ["google", "linkedin", "github"] as const

// LinkedIn signs in through OpenID Connect (Firebase with Identity Platform).
export const LINKEDIN_PROVIDER_ID = "oidc.linkedin"

// The email already has an account under another way of signing in.
export const ACCOUNT_EXISTS = "auth/account-exists-with-different-credential"

// Set once someone has signed in on this browser: the sign-in card then leaves out the email
// choices a new account makes.
export const SIGNED_IN_BEFORE_KEY = "prepza:signed-in-before"
