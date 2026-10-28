"use client"

import { cn } from "cn"
import { useTranslations } from "next-intl"
import { useEffect, useState } from "react"
import { toast } from "sonner"

import { QuestionRow } from "@/components/common/question-row"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { VirtualList } from "@/components/common/virtual-list"
import { WarningCard } from "@/components/common/warning-card"
import { apiFetch, serviceRefusal } from "@/lib/api"
import { languageOf } from "@/lib/locale"
import type { QuestionStats } from "@/types/feedback"

/** A topic's questions in a dialog, written in `language` (the interview's or template's). */
export function TopicQuestions({
  title,
  language,
  path,
  regeneratePath,
  wrongPath,
  reportsPath,
}: {
  title: string
  language: string
  path: string
  regeneratePath?: string
  wrongPath?: string
  reportsPath?: string
}) {
  const t = useTranslations("questions")
  const common = useTranslations("common")
  const [open, setOpen] = useState(false)
  const [questions, setQuestions] = useState<QuestionStats[] | null>(null)
  const [missing, setMissing] = useState(false)
  const [regeneratingId, setRegeneratingId] = useState<string | null>(null)

  useEffect(() => {
    if (!open || questions) {
      return
    }

    let cancelled = false

    apiFetch<QuestionStats[]>(path)
      .then((rows) => {
        if (!cancelled) {
          setQuestions(rows)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setMissing(true)
        }
      })

    return () => {
      cancelled = true
    }
  }, [open, questions, path])

  async function regenerate(questionId: string) {
    setRegeneratingId(questionId)

    try {
      const fresh = await apiFetch<{ id: string; text: string }>(
        `${regeneratePath}/${questionId}/regenerate`,
        { method: "POST" }
      )
      setQuestions((rows) =>
        (rows ?? []).map((row) =>
          row.id === questionId
            ? { ...row, text: fresh.text, likes: 0, dislikes: 0, reports: 0 }
            : row
        )
      )
      toast.success(t("regenerated"))
    } catch (error) {
      toast.error(
        // A daily limit or the emergency pause explains itself; anything else is generic.
        serviceRefusal(error, [429, 503]) ?? t("regenerateFailed")
      )
    } finally {
      setRegeneratingId(null)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        data-testid="manage-questions"
        render={<Button variant="outline" className="h-9 shrink-0 px-4" />}
      >
        {t("manage")}
      </DialogTrigger>
      <DialogContent
        showCloseButton={false}
        // On phones it fills the screen, the questions taking the height left, with the
        // warning and the list out to the screen's edges.
        className={cn(
          "max-sm:h-dvh max-sm:gap-6",
          regeneratePath ? "sm:max-w-4xl" : "sm:max-w-3xl"
        )}
      >
        <DialogHeader>
          <DialogTitle className="normal-case" {...languageOf(language)}>
            {title}
          </DialogTitle>
        </DialogHeader>
        {/* Owners should know the keys can be wrong (the AI Act's instructions for use); the
            warning card the templates page used to have. */}
        <WarningCard className="max-sm:-mx-10 max-sm:rounded-none">
          {t("aiWritten")}
        </WarningCard>
        {questions ? (
          <VirtualList
            items={questions}
            getKey={(question) => question.id}
            // A question with its four answer options.
            estimateSize={200}
            scrollClassName="max-h-[60vh] overflow-y-auto rounded-xl border max-sm:-mx-10 max-sm:max-h-none max-sm:min-h-0 max-sm:flex-1 max-sm:rounded-none max-sm:border-x-0"
            className="divide-y"
            renderItem={(question) => (
              <QuestionRow
                question={question}
                language={language}
                canRegenerate={Boolean(regeneratePath)}
                wrongPath={wrongPath}
                reportsPath={reportsPath}
                regenerating={regeneratingId === question.id}
                busy={regeneratingId !== null}
                onRegenerate={() => regenerate(question.id)}
              />
            )}
          />
        ) : (
          <p className="text-muted-foreground">
            {missing ? t("loadFailed") : common("loading")}
          </p>
        )}
        <DialogFooter showCloseButton />
      </DialogContent>
    </Dialog>
  )
}
