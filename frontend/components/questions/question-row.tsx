"use client"

import {
  CircleAlertIcon,
  FlagIcon,
  RefreshCwIcon,
  ThumbsDownIcon,
  ThumbsUpIcon,
} from "lucide-react"
import { cn } from "cn"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { AnswerOptions } from "@/components/questions/answer-options"
import { QuestionReports } from "@/components/questions/question-reports"
import { MultiChoiceTag } from "@/components/questions/multi-choice-tag"
import { QuestionText } from "@/components/questions/question-text"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { apiFetch } from "@/lib/api"
import { languageOf } from "@/lib/locale"
import { FEEDBACK_HOVER_CLASS } from "@/constants/feedback"
import type { QuestionStats } from "@/types/feedback"

export function QuestionRow({
  question,
  language,
  canRegenerate,
  wrongPath,
  reportsPath,
  regenerating,
  busy,
  onRegenerate,
}: {
  question: QuestionStats
  // What the question is written in; its text and options carry it.
  language: string
  canRegenerate: boolean
  // Where to say the marked answer is wrong (owners and admins, superadmins).
  wrongPath?: string
  reportsPath?: string
  regenerating: boolean
  busy: boolean
  onRegenerate: () => void
}) {
  const t = useTranslations("questions")
  const [showReports, setShowReports] = useState(false)
  const [markedWrong, setMarkedWrong] = useState(false)

  // One click: the verifier checks the marked answer and fixes or replaces the question.
  async function markWrong() {
    setMarkedWrong(true)

    try {
      await apiFetch(`${wrongPath}/${question.id}/wrong`, { method: "POST" })
      toast.success(t("markedWrong"))
    } catch {
      setMarkedWrong(false)
      toast.error(t("markWrongFailed"))
    }
  }
  const canViewReports = Boolean(reportsPath)

  return (
    // Columns: the question, then feedback and actions (on phones, centered on the line under
    // it); reports open in a row below.
    <div className="grid grid-cols-[1fr_auto] max-sm:grid-cols-1">
      <div
        className={cn(
          "min-w-0 px-5 py-5 font-light max-sm:pt-7",
          regenerating && "opacity-50"
        )}
      >
        <div {...languageOf(language)}>
          <QuestionText text={question.text} />
        </div>
        {/* Candidates tick every right option of it. */}
        {question.multi && (
          <div className="mt-3">
            <MultiChoiceTag />
          </div>
        )}
        <div {...languageOf(language)}>
          <AnswerOptions options={question.options} className="mt-3" />
        </div>
      </div>
      <div className="self-center py-5 ps-5 pe-6 text-sm whitespace-nowrap text-muted-foreground tabular-nums max-sm:px-5 max-sm:pt-0 max-sm:pb-7">
        <span className="flex flex-col items-end gap-3 max-sm:items-center">
          <span className="flex items-center gap-4">
            <Tooltip>
              <TooltipTrigger
                render={<span className="flex items-center gap-1.5" />}
              >
                <ThumbsUpIcon className="size-4" />
                {question.likes}
              </TooltipTrigger>
              <TooltipContent>{t("likes")}</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger
                render={<span className="flex items-center gap-1.5" />}
              >
                <ThumbsDownIcon className="size-4" />
                {question.dislikes}
              </TooltipTrigger>
              <TooltipContent>{t("dislikes")}</TooltipContent>
            </Tooltip>
            {canViewReports ? (
              <Tooltip>
                <TooltipTrigger
                  render={
                    <button
                      type="button"
                      aria-expanded={showReports}
                      onClick={() => setShowReports((shown) => !shown)}
                      aria-label={t("showReports", { count: question.reports })}
                      className={cn(
                        "-mx-2 -my-1 flex cursor-pointer items-center gap-1.5 rounded-md px-2 py-1 aria-expanded:bg-foreground/10 aria-expanded:text-foreground",
                        FEEDBACK_HOVER_CLASS
                      )}
                    />
                  }
                >
                  <FlagIcon className="size-4" />
                  {question.reports}
                </TooltipTrigger>
                <TooltipContent>{t("reports")}</TooltipContent>
              </Tooltip>
            ) : (
              <Tooltip>
                <TooltipTrigger
                  render={<span className="flex items-center gap-1.5" />}
                >
                  <FlagIcon className="size-4" />
                  {question.reports}
                </TooltipTrigger>
                <TooltipContent>{t("reports")}</TooltipContent>
              </Tooltip>
            )}
          </span>
          {/* Under each other, beside the question; on one line, on phones. */}
          <span className="flex flex-col items-end gap-3 max-sm:flex-row">
            {canRegenerate && (
              <Button variant="outline" disabled={busy} onClick={onRegenerate}>
                <RefreshCwIcon
                  data-icon="inline-start"
                  className={cn(regenerating && "animate-spin")}
                />
                {regenerating ? t("regenerating") : t("regenerate")}
              </Button>
            )}
            {wrongPath && (
              <Button
                variant="outline"
                disabled={busy || markedWrong}
                onClick={markWrong}
              >
                <CircleAlertIcon data-icon="inline-start" />
                {markedWrong ? t("checking") : t("wrongAnswer")}
              </Button>
            )}
          </span>
        </span>
      </div>
      {canViewReports && showReports && (
        <div className="col-span-full bg-muted/40 py-5 ps-5 pe-6">
          <QuestionReports path={`${reportsPath}/${question.id}/reports`} />
        </div>
      )}
    </div>
  )
}
