"use client"

import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { WritingProgress } from "@/components/generation/writing-progress"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { ACTIVE_STATUSES } from "@/config/generation"
import { useGenerationPoll } from "@/hooks/use-generation-poll"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import type { Addition } from "@/types/generation"
import { CARD } from "@/config/cards"

/** A superadmin adds questions to every topic of a template: "Top up" (when the backend says a
 * topic lacks practice or company questions) writes what's missing, "Add questions" a number of
 * the superadmin's choice, which the backend checks and splits. Either runs in the background;
 * its progress shows here, and the counts refresh once it's done. */
export function TemplateAdditions({
  templateId,
  short,
  initial,
}: {
  templateId: string
  short: boolean
  initial: Addition
}) {
  const t = useTranslations("superadmin")
  const common = useTranslations("common")
  const router = useRouter()
  const path = `/generate/superadmin/templates/${templateId}`
  const [addition, setAddition] = useState(initial)
  // Bumped after a start so polling begins again.
  const [round, setRound] = useState(0)
  const [open, setOpen] = useState(false)
  const [count, setCount] = useState(String(initial.default_count))
  const [starting, setStarting] = useState(false)
  const running =
    addition.status != null && ACTIVE_STATUSES.includes(addition.status)

  useGenerationPoll<Addition>(
    running ? `${path}/additions/latest` : null,
    round,
    (next) => {
      setAddition(next)

      if (next.status === "done") {
        toast.success(t("questionsAdded"))
        router.refresh()
      } else if (next.status === "failed") {
        toast.error(next.error ?? t("addQuestionsFailed"))
      }
    }
  )

  async function start(url: string, body?: object) {
    setStarting(true)

    try {
      const next = await apiFetch<Addition>(url, {
        method: "POST",
        body: body ? JSON.stringify(body) : undefined,
      })
      setAddition(next)
      setOpen(false)
      setRound((value) => value + 1)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("addQuestionsFailed")))
    } finally {
      setStarting(false)
    }
  }

  if (running) {
    return (
      <div
        className={`basis-full space-y-4 ${CARD} text-center`}
        data-testid="adding-questions"
      >
        <p className="text-lg font-medium">{t("addingQuestions")}</p>
        {addition.progress && addition.progress.total > 0 && (
          <WritingProgress progress={addition.progress} />
        )}
      </div>
    )
  }

  return (
    <div className="flex gap-3 max-sm:basis-full max-sm:flex-col max-sm:items-stretch">
      {short && (
        <Button
          variant="outline"
          className="h-10 px-5 text-base"
          disabled={starting}
          onClick={() => start(`${path}/top-up`)}
          data-testid="top-up"
        >
          {t("topUp")}
        </Button>
      )}
      <Button
        className="h-10 px-5 text-base"
        data-testid="add-questions"
        onClick={() => {
          setCount(String(addition.default_count))
          setOpen(true)
        }}
      >
        {t("addQuestions")}
      </Button>
      <Dialog open={open} onOpenChange={(next) => !starting && setOpen(next)}>
        <DialogContent showCloseButton={false} className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{t("addQuestionsTitle")}</DialogTitle>
            <DialogDescription>{t("addQuestionsText")}</DialogDescription>
          </DialogHeader>
          <form
            id="add-questions-form"
            onSubmit={(event) => {
              event.preventDefault()
              start(`${path}/additions`, { count: Number(count) })
            }}
          >
            <div className="relative rounded-xl border border-transparent transition-colors focus-within:border-ring-gradient">
              <Input
                required
                type="number"
                inputMode="numeric"
                min={addition.count_step}
                max={addition.max_count}
                step={addition.count_step}
                aria-label={t("addQuestionsCount")}
                value={count}
                onChange={(event) => setCount(event.target.value)}
                className="h-16 border-0 px-6 text-lg focus-visible:ring-0 md:text-lg"
              />
            </div>
          </form>
          <DialogFooter>
            <DialogClose
              render={
                <Button
                  variant="outline"
                  className="h-10 px-5 text-base"
                  disabled={starting}
                />
              }
            >
              {common("cancel")}
            </DialogClose>
            <Button
              type="submit"
              form="add-questions-form"
              className="h-10 px-5 text-base"
              disabled={starting}
            >
              {t("add")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
