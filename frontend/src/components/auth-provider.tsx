"use client"

import * as Sentry from "@sentry/nextjs"
import type { User } from "firebase/auth"
import { useRouter } from "next/navigation"
import { createContext, useContext, useEffect, useState } from "react"

import { apiFetch } from "@/lib/api"
import { readTokenCookie, writeTokenCookie } from "@/lib/auth"
import { firebaseAuth } from "@/lib/firebase"
import { isLocale, readLocaleCookie, writeLocaleCookie } from "@/lib/locale"
import { SIGNED_IN_BEFORE_KEY } from "@/constants/auth"
import type { AuthState } from "@/types/auth"

const AuthContext = createContext<AuthState>({ user: null, loading: true })

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [state, setState] = useState<AuthState>({ user: null, loading: true })

  useEffect(() => {
    // Firebase loads after the page is up, so pages show without waiting for it.
    let unsubscribe: (() => void) | undefined
    let stopped = false

    Promise.all([firebaseAuth(), import("firebase/auth")]).then(
      ([auth, { onIdTokenChanged }]) => {
        if (stopped) {
          return
        }

        unsubscribe = onIdTokenChanged(auth, onChange)
      }
    )

    async function onChange(user: User | null) {
      const token = user ? await user.getIdToken() : null
      // Firebase reports the restored session on every page load; the pages were already
      // rendered with that token, so they re-render only when the token or language changes.
      let changed = token !== readTokenCookie()

      if (changed) {
        writeTokenCookie(token)
      }

      // The interface follows the account's language, also on a new device.
      if (user) {
        const { claims } = await user.getIdTokenResult()
        const language = String(claims.language ?? "")

        if (isLocale(language) && language !== readLocaleCookie()) {
          writeLocaleCookie(language)
          changed = true
        }

        // A new account keeps the language it signed up in, for the interface and its emails.
        // The refreshed token carries it, and this runs again with it.
        if (!claims.language && isLocale(document.documentElement.lang)) {
          await apiFetch("/library/me/settings", {
            method: "PUT",
            body: JSON.stringify({ language: document.documentElement.lang }),
          })
            .then(() => user.getIdToken(true))
            .catch(() => {})
        }
      }

      // The sign-in card leaves out a new account's email choices from now on (sign-in-options.tsx).
      if (user) {
        try {
          localStorage.setItem(SIGNED_IN_BEFORE_KEY, "1")
        } catch {}
      }

      // Errors name the account by id only, never by email.
      Sentry.setUser(user ? { id: user.uid } : null)
      setState({ user, loading: false })

      // Server-rendered pages read the token cookie, so re-render them with the new one.
      if (changed) {
        router.refresh()
      }
    }

    return () => {
      stopped = true
      unsubscribe?.()
    }
  }, [router])

  return <AuthContext value={state}>{children}</AuthContext>
}

export function useAuth() {
  return useContext(AuthContext)
}
