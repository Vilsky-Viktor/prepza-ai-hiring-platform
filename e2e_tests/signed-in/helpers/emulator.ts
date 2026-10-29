import { AUTH_URL } from "../constants"
import { env } from "./env"

// The emulator takes any key, and "owner" as an admin's token.
const KEY = "key=demo"
const ADMIN = { Authorization: "Bearer owner" }

/** A sign-in the emulator gave: what the site's Firebase keeps for a signed-in user. */
export type EmulatorSession = {
  uid: string
  email: string
  displayName: string
  idToken: string
  refreshToken: string
  expiresIn: number
}

type EmulatorAccount = {
  displayName?: string
  providerUserInfo?: { providerId: string; rawId: string }[]
}

async function call<T>(path: string, body: object, headers: object = {}): Promise<T> {
  const response = await fetch(`${AUTH_URL}/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    throw new Error(`emulator ${path} -> ${response.status}: ${await response.text()}`)
  }

  return response.json() as Promise<T>
}

/** The emulator's account for `email`, if it has one. */
async function account(email: string): Promise<EmulatorAccount | undefined> {
  const project = env("FIREBASE_PROJECT_ID")
  const found = await call<{ users?: EmulatorAccount[] }>(
    `identitytoolkit.googleapis.com/v1/projects/${project}/accounts:lookup`,
    { email: [email] },
    ADMIN
  )

  return found.users?.[0]
}

/** Signs in with Google at the emulator straight away, as its sign-in page does once an account
 * is picked: the emulator takes an unsigned Google ID token (never the real Google). An existing
 * account keeps its Google id and name; a new one is named `displayName`. */
export async function googleSignIn(email: string, displayName: string): Promise<EmulatorSession> {
  const existing = await account(email)
  const google = existing?.providerUserInfo?.find((info) => info.providerId === "google.com")
  const name = existing ? (existing.displayName ?? "") : displayName
  const claims = {
    sub: google?.rawId ?? `e2e-${email}`,
    email,
    email_verified: true,
    ...(name ? { name } : {}),
  }
  const signedIn = await call<{
    localId: string
    idToken: string
    refreshToken: string
    expiresIn: string
  }>(`identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?${KEY}`, {
    postBody: `id_token=${encodeURIComponent(JSON.stringify(claims))}&providerId=google.com`,
    requestUri: "http://localhost",
    returnSecureToken: true,
  })

  return {
    uid: signedIn.localId,
    email,
    displayName: name,
    idToken: signedIn.idToken,
    refreshToken: signedIn.refreshToken,
    expiresIn: Number(signedIn.expiresIn),
  }
}

/** A new ID token for the session, carrying the claims set since it was issued. */
export async function refreshed(session: EmulatorSession): Promise<EmulatorSession> {
  const response = await fetch(`${AUTH_URL}/securetoken.googleapis.com/v1/token?${KEY}`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `grant_type=refresh_token&refresh_token=${encodeURIComponent(session.refreshToken)}`,
  })

  if (!response.ok) {
    throw new Error(`emulator token refresh -> ${response.status}`)
  }

  const body = await response.json()

  return { ...session, idToken: body.id_token, refreshToken: body.refresh_token }
}
