import type { Auth } from "firebase/auth"

let loading: Promise<Auth> | undefined

/** Firebase Auth, loaded on first use rather than with every page: auth-provider.tsx asks for
 * it once the page is up, so it's ready before anyone clicks to sign in. */
export function firebaseAuth() {
  loading ??= Promise.all([
    import("firebase/app"),
    import("firebase/auth"),
  ]).then(
    ([
      { initializeApp },
      { connectAuthEmulator, getAuth, initializeAuth, inMemoryPersistence },
    ]) => {
      const app = initializeApp({
        apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
        authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
        projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
      })
      // Framed in a company's site (the embedded interview), the guest's sign-in stays in memory:
      // the frame's storage is partitioned per site, can be wiped (Safari) or stall, and the
      // interview resumes from the server by its link anyway.
      const auth =
        window.top !== window.self
          ? initializeAuth(app, { persistence: inMemoryPersistence })
          : getAuth(app)
      const emulatorUrl = process.env.NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL

      if (emulatorUrl) {
        // On the host the page was opened from, so a phone on the same network reaches it too.
        const url = new URL(emulatorUrl)
        url.hostname = window.location.hostname
        connectAuthEmulator(auth, url.origin, { disableWarnings: true })
      }

      return auth
    }
  )

  return loading
}
