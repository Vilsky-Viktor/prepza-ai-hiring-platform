"use client"

import { useEffect, useState } from "react"

import { SILENT_WAV } from "@/config/voice"
import { recordingType } from "@/lib/voice"
import { openMicrophone } from "@/lib/voice-listening"

// The voice interview's access, asked for on its start page: not yet asked, being asked,
// granted, refused, or a browser that can't record.
export type VoiceAccess =
  "ask" | "asking" | "granted" | "denied" | "unsupported"

/** A voice interview's microphone and sound, allowed before it starts. A microphone already
 * allowed (or refused) for the site is known at once where the browser says; the tap on the
 * allow button also lets the page play sound. `on`: the interview is taken by voice. */
export function useVoiceAccess(on: boolean) {
  const [access, setAccess] = useState<VoiceAccess>("ask")

  useEffect(() => {
    if (!on || !navigator.permissions) {
      return
    }

    navigator.permissions
      .query({ name: "microphone" as PermissionName })
      .then((permission) => {
        if (permission.state === "granted") {
          setAccess("granted")
        }

        if (permission.state === "denied") {
          setAccess("denied")
        }
      })
      // Browsers that can't tell (Firefox): the button asks.
      .catch(() => undefined)
  }, [on])

  async function allow() {
    if (!recordingType()) {
      setAccess("unsupported")

      return
    }

    setAccess("asking")
    void new Audio(SILENT_WAV).play().catch(() => undefined)

    try {
      const microphone = await openMicrophone()
      microphone.getTracks().forEach((track) => track.stop())
      setAccess("granted")
    } catch {
      setAccess("denied")
    }
  }

  return { access, allow }
}
