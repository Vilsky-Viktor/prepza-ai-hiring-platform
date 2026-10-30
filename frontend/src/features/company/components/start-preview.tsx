"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { apiErrorMessage, apiFetch } from "@/lib/api"
import { StartPledge } from "@/features/company/components/start-pledge"

/** The preview's "accept & start": a free run of the test as a candidate, kept out of the
 * candidate list; the player links back to the test it came from. */
export function StartPreview({
  companyId,
  interviewId,
  voice,
}: {
  companyId: string
  interviewId: string
  // Taken by voice: the microphone and sound are allowed first.
  voice: boolean
}) {
  const t = useTranslations("invite")
  const interviews = useTranslations("interviews")
  const router = useRouter()
  const [starting, setStarting] = useState(false)

  async function start(pledged: boolean) {
    setStarting(true)

    try {
      const preview = await apiFetch<{ session_id: string }>(
        `/companies/interviews/${interviewId}/preview`,
        { method: "POST", body: JSON.stringify({ pledged }) }
      )
      router.push(
        `/sessions/${preview.session_id}?from=/companies/${companyId}/interviews/${interviewId}`
      )
    } catch (error) {
      toast.error(apiErrorMessage(error, interviews("tryFailed")))
      setStarting(false)
    }
  }

  return (
    <StartPledge
      label={t("start")}
      pledge
      busy={starting}
      onStart={start}
      testId="accept-start"
      voice={voice}
    />
  )
}
