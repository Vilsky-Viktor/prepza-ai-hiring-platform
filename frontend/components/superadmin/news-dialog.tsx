"use client"

import { useTranslations } from "next-intl"
import { useId, useState } from "react"
import { toast } from "sonner"

import { LabeledField } from "@/components/labeled-field"
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
import { Textarea } from "@/components/ui/textarea"
import { MAX_NEWS_TEXT_LENGTH, MAX_NEWS_TITLE_LENGTH } from "@/constants/limits"
import { apiErrorMessage, apiFetch } from "@/lib/api"
import { today } from "@/lib/format"
import type { AdminNewsPost } from "@/types/news"
import { GRAY_FIELD } from "@/constants/fields"

/** Writes a news post in English, or edits `post`: its title, day (today for a new one) and
 * text, with how many characters the text has left. The API checks the limits. */
export function NewsDialog({
  open,
  onOpenChange,
  post,
  onSaved,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  post?: AdminNewsPost
  onSaved: (post: AdminNewsPost) => void
}) {
  const t = useTranslations("superadmin")
  const common = useTranslations("common")
  const [title, setTitle] = useState(post?.title ?? "")
  const [day, setDay] = useState(post?.published_on ?? today())
  const [text, setText] = useState(post?.text ?? "")
  const [saving, setSaving] = useState(false)
  const textId = useId()

  async function save(event: React.FormEvent) {
    event.preventDefault()
    setSaving(true)

    try {
      const saved = await apiFetch<AdminNewsPost>(
        post
          ? `/library/superadmin/news/${post.id}`
          : "/library/superadmin/news",
        {
          method: post ? "PUT" : "POST",
          body: JSON.stringify({ title, text, published_on: day }),
        }
      )
      onSaved(saved)
      onOpenChange(false)
    } catch (error) {
      toast.error(apiErrorMessage(error, t("postSaveFailed")))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !saving && onOpenChange(next)}>
      <DialogContent showCloseButton={false} className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{post ? t("editPost") : t("newPost")}</DialogTitle>
          <DialogDescription>{t("postInEnglish")}</DialogDescription>
        </DialogHeader>
        <form id="news-post" onSubmit={save} className="min-w-0 space-y-4">
          <LabeledField label={common("title")}>
            <Input
              required
              maxLength={MAX_NEWS_TITLE_LENGTH}
              placeholder={t("postTitlePlaceholder")}
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              className={`h-14 ${GRAY_FIELD}`}
            />
          </LabeledField>
          <LabeledField label={t("postDate")}>
            <Input
              required
              type="date"
              value={day}
              onChange={(event) => setDay(event.target.value)}
              className={`h-14 w-auto ${GRAY_FIELD}`}
            />
          </LabeledField>
          <LabeledField label={t("postText")} htmlFor={textId}>
            <Textarea
              required
              id={textId}
              maxLength={MAX_NEWS_TEXT_LENGTH}
              placeholder={t("postTextPlaceholder")}
              value={text}
              onChange={(event) => setText(event.target.value)}
              // A long unbroken word wraps instead of widening the dialog.
              className={`min-h-48 resize-none rounded-xl py-4 wrap-anywhere ${GRAY_FIELD}`}
            />
            <p
              aria-live="polite"
              className="text-end text-sm text-muted-foreground tabular-nums"
            >
              {t("charactersLeft", {
                count: MAX_NEWS_TEXT_LENGTH - text.length,
              })}
            </p>
          </LabeledField>
        </form>
        <DialogFooter>
          <DialogClose
            render={
              <Button
                variant="outline"
                className="h-10 px-5 text-base"
                disabled={saving}
              />
            }
          >
            {common("cancel")}
          </DialogClose>
          <Button
            type="submit"
            form="news-post"
            className="h-10 px-5 text-base"
            disabled={saving}
          >
            {saving ? common("saving") : common("save")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
