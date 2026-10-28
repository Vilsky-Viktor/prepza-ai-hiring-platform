"use client"

import { useEffect } from "react"
import { preconnect } from "react-dom"

import { TURNSTILE_ORIGINS } from "@/config/security"
import { prepareHumanCheck } from "@/lib/human-check"

/** For a form whose request passes Turnstile's check (lib/human-check.ts): connects to
 * Cloudflare and gets the widget ready as the form appears, so sending it only runs the check.
 * `needed` false (a signed-in person's assistant) leaves Turnstile out. */
export function useHumanCheck(needed = true) {
  if (needed) {
    for (const origin of TURNSTILE_ORIGINS) {
      preconnect(origin)
    }
  }

  useEffect(() => {
    if (needed) {
      void prepareHumanCheck()
    }
  }, [needed])
}
