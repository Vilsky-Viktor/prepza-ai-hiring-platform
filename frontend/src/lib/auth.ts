import type { FirebaseError } from "firebase/app"
import type { AuthCredential, AuthProvider } from "firebase/auth"

import {
  ACCOUNT_EXISTS,
  LINKEDIN_PROVIDER_ID,
  POPUP_CLOSED_CODES,
  TOKEN_COOKIE,
  TOKEN_COOKIE_MAX_AGE,
} from "@/config/auth"
import { firebaseAuth } from "@/lib/firebase"
import type { SignInProvider, SignInResult } from "@/types/sign-in"

// A way of signing in that met an existing account with the same email, waiting to be linked
// once its owner signs in the way they did before.
let pending: { credential: AuthCredential; email: string } | null = null

// Firebase's sign-in functions, loaded with Firebase itself (lib/firebase.ts).
type Firebase = typeof import("firebase/auth")

function providerFor(firebase: Firebase, name: SignInProvider): AuthProvider {
  if (name === "github") {
    const github = new firebase.GithubAuthProvider()
    github.addScope("user:email")

    return github
  }

  if (name === "linkedin") {
    const linkedin = new firebase.OAuthProvider(LINKEDIN_PROVIDER_ID)
    linkedin.addScope("openid")
    linkedin.addScope("profile")
    linkedin.addScope("email")

    return linkedin
  }

  return new firebase.GoogleAuthProvider()
}

function credentialFrom(
  firebase: Firebase,
  name: SignInProvider,
  error: FirebaseError
) {
  if (name === "github") {
    return firebase.GithubAuthProvider.credentialFromError(error)
  }

  if (name === "linkedin") {
    return firebase.OAuthProvider.credentialFromError(error)
  }

  return firebase.GoogleAuthProvider.credentialFromError(error)
}

/** Signs in with one of the ways offered. One account per email: when the email already has
 * one under another way, this way is kept and linked once the person signs in as before. */
export async function signIn(name: SignInProvider): Promise<SignInResult> {
  // Already loaded by auth-provider.tsx, so the popup still opens from the click.
  const [auth, firebase, app] = await Promise.all([
    firebaseAuth(),
    import("firebase/auth"),
    import("firebase/app"),
  ])

  try {
    const { user } = await firebase.signInWithPopup(
      auth,
      providerFor(firebase, name)
    )

    if (pending && pending.email === user.email) {
      await firebase
        .linkWithCredential(user, pending.credential)
        .catch(() => {})
    }

    pending = null

    // Invites need a verified email; some ways of signing in (GitHub) don't verify it, so a
    // link is sent to confirm it. Each sign-in sends a new one, so a failed send is said.
    if (!user.emailVerified) {
      const sent = await firebase.sendEmailVerification(user).then(
        () => true,
        () => false
      )

      return sent ? "verify" : "verifyFailed"
    }

    return "done"
  } catch (error) {
    if (!(error instanceof app.FirebaseError)) {
      return "failed"
    }

    if (POPUP_CLOSED_CODES.includes(error.code)) {
      return "cancelled"
    }

    const credential = credentialFrom(firebase, name, error)
    const email = (error.customData?.email as string | undefined) ?? null

    if (error.code === ACCOUNT_EXISTS && credential && email) {
      pending = { credential, email }

      return "link"
    }

    return "failed"
  }
}

/** Signs in as the guest a company's own platform sent with the invite link: no account, no
 * email, only that interview (the token comes from companies). */
export async function signInAsGuest(token: string) {
  const [auth, firebase] = await Promise.all([
    firebaseAuth(),
    import("firebase/auth"),
  ])
  await firebase.signInWithCustomToken(auth, token)
}

/** An email verified since signing in (the link sent then, opened in another tab) counts at once:
 * the account is read again and, once verified, a new token says so. */
export async function refreshVerification() {
  const user = (await firebaseAuth()).currentUser

  if (!user || user.emailVerified) {
    return
  }

  await user.reload().catch(() => {})

  if (user.emailVerified) {
    await user.getIdToken(true).catch(() => {})
  }
}

export async function signOut() {
  const [auth, { signOut }] = await Promise.all([
    firebaseAuth(),
    import("firebase/auth"),
  ])

  return signOut(auth)
}

export function readTokenCookie() {
  return (
    document.cookie
      .split("; ")
      .find((item) => item.startsWith(`${TOKEN_COOKIE}=`))
      ?.split("=")[1] || null
  )
}

export function writeTokenCookie(token: string | null) {
  const maxAge = token ? TOKEN_COOKIE_MAX_AGE : 0
  const secure = location.protocol === "https:" ? "; secure" : ""
  document.cookie = `${TOKEN_COOKIE}=${token ?? ""}; path=/; max-age=${maxAge}; samesite=lax${secure}`
}
