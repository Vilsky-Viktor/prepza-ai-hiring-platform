"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { useSignIn } from "@/components/sign-in-dialog"
import { useAuth } from "@/providers/auth-provider"
import { PracticeTiming } from "@/components/practice/practice-timing"
import { Button } from "@/components/ui/button"
import { apiErrorMessage, serviceRefusal } from "@/lib/api"
import { startPracticeRound } from "@/lib/practice"
import type { PracticeTiming as Timing, PracticeTimingId } from "@/types/round"

/** Starts a free practice round on the template with the time per question the talent picks
 * from `timings` (standard by default): signs in first when needed, then goes straight into the
 * round. `label` names it (start, or practise again). */
export function StartPractice({
  templateId,
  label,
  timings,
}: {
  templateId: string
  label: string
  timings: Timing[]
}) {
  const t = useTranslations("practice")
  const signIn = useSignIn()
  const router = useRouter()
  const { user } = useAuth()
  const [starting, setStarting] = useState(false)
  const [timing, setTiming] = useState<PracticeTimingId>("standard")

  async function start() {
    setStarting(true)

    if (!user && !(await signIn())) {
      setStarting(false)

      return
    }

    try {
      router.push(await startPracticeRound(templateId, timing))
    } catch (error) {
      // No practice questions yet: the API says so.
      toast.error(
        serviceRefusal(error, [409]) ?? apiErrorMessage(error, t("startFailed"))
      )
      setStarting(false)
    }
  }

  return (
    <div className="flex items-center gap-3 max-sm:*:flex-1">
      <PracticeTiming
        timings={timings}
        value={timing}
        onChange={setTiming}
        disabled={starting}
      />
      <Button
        className="h-12 px-6 text-base"
        disabled={starting}
        data-testid="start-practice"
        onClick={start}
      >
        {label}
      </Button>
    </div>
  )
}
