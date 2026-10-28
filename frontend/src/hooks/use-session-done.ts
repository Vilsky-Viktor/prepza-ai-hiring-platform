"use client"

import { useRouter } from "next/navigation"
import { useEffect } from "react"

/** Once a test is finished: embedded in a company's site, `onFinished` is told (which takes the
 * candidate on); a practice round opens its results with every answer. */
export function useSessionDone(
  done: boolean,
  inviteId: string | null | undefined,
  practice: boolean,
  onFinished?: (candidateId: string) => void
) {
  const router = useRouter()

  useEffect(() => {
    if (done && inviteId && onFinished) {
      onFinished(inviteId)
    }
  }, [done, inviteId, onFinished])

  const practiceDone = practice && done

  useEffect(() => {
    if (practiceDone) {
      router.replace(`/practice/rounds/${inviteId}`)
    }
  }, [practiceDone, inviteId, router])
}
