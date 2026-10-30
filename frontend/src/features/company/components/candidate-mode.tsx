"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { AnswerModeSetting } from "@/features/company/components/answer-mode-switch"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { LIST_BOX } from "@/config/lists"

/** How one candidate takes the interview, by click or voice, apart from the interview's mode:
 * the settings' switch in a card of its own, shown only while the API lets the user change it
 * (`editable`: before the candidate starts); afterwards nothing, as the mode is fixed. */
export function CandidateMode({
  interviewId,
  inviteId,
  voice,
  editable,
}: {
  interviewId: string
  inviteId: string
  voice: boolean
  editable: boolean
}) {
  const t = useTranslations("candidates")
  const interviews = useTranslations("interviews")
  const router = useRouter()
  const [current, setCurrent] = useState(voice)
  const [saving, setSaving] = useState(false)

  async function choose(next: boolean) {
    setSaving(true)

    try {
      await apiFetch(
        `/companies/interviews/${interviewId}/candidates/${inviteId}/voice`,
        { method: "PUT", body: JSON.stringify({ voice: next }) }
      )
      setCurrent(next)
      router.refresh()
    } catch (error) {
      toast.error(apiErrorMessage(error, t("modeFailed")))
    } finally {
      setSaving(false)
    }
  }

  if (!editable) {
    return null
  }

  return (
    <div className={LIST_BOX} data-testid="candidate-mode">
      <AnswerModeSetting
        label={interviews("answerMode")}
        help={t("modeHelp")}
        voice={current}
        disabled={saving}
        onChange={choose}
      />
    </div>
  )
}
