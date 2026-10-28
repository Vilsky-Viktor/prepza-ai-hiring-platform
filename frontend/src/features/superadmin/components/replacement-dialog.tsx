"use client"

import { useTranslations } from "next-intl"

import { AnswerOptions } from "@/components/common/answer-options"
import { QuestionText } from "@/components/common/question-text"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"

/** A replaced question's button that shows, in a dialog, the question that took its place. */
export function ReplacementDialog({
  text,
  options,
}: {
  text: string
  options: { answer: string; correct: boolean }[]
}) {
  const t = useTranslations("superadmin")
  const common = useTranslations("common")

  return (
    <Dialog>
      <DialogTrigger
        data-testid="replaced-with"
        render={
          <Button variant="outline" size="sm" className="h-8 px-3 text-sm" />
        }
      >
        {t("replacedWith")}
      </DialogTrigger>
      <DialogContent showCloseButton={false} className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("replacedWith")}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <QuestionText text={text} className="font-light" />
          <AnswerOptions options={options} className="space-y-2" />
        </div>
        <DialogFooter>
          <DialogClose
            render={
              <Button variant="outline" className="h-10 px-5 text-base" />
            }
          >
            {common("close")}
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
