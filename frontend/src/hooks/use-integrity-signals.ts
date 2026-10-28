import { useEffect } from "react"

import { apiFetch } from "@/lib/api"

/** Tells the server when the candidate leaves the page or copies, for the company's scorecard,
and how long a leave lasted once they're back (the server decides whether it counts).

Reporting never gets in the candidate's way: a failed report is dropped. */
export function useIntegritySignals(sessionId: string, active: boolean) {
  useEffect(() => {
    if (!active) {
      return
    }

    // When the current leave began, while the candidate is away.
    let leftAt: number | null = null

    function report(
      kind: "tab_leave" | "tab_return" | "copy",
      seconds?: number
    ) {
      apiFetch(`/rounds/sessions/${sessionId}/signals`, {
        method: "POST",
        body: JSON.stringify({ kind, seconds }),
      }).catch(() => {})
    }

    // Blur covers both another tab and another app.
    function onBlur() {
      leftAt = Date.now()
      report("tab_leave")
    }

    function onFocus() {
      if (leftAt === null) {
        return
      }

      report("tab_return", (Date.now() - leftAt) / 1000)
      leftAt = null
    }

    const onCopy = () => report("copy")

    window.addEventListener("blur", onBlur)
    window.addEventListener("focus", onFocus)
    document.addEventListener("copy", onCopy)

    return () => {
      window.removeEventListener("blur", onBlur)
      window.removeEventListener("focus", onFocus)
      document.removeEventListener("copy", onCopy)
    }
  }, [sessionId, active])
}
