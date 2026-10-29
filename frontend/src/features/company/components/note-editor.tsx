"use client"

import { useTranslations } from "next-intl"
import { type FormEvent, useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { FloatingTextarea } from "@/components/ui/floating-field"
import { MAX_NOTE_LENGTH } from "@/config/limits"
import { apiErrorMessage, serviceRefusal } from "@/lib/api"
import { SubmitHint } from "@/components/common/submit-hint"
import { isSubmitShortcut } from "@/lib/keys"

/** A note's text box with its button: Enter adds a line, ⌘/Ctrl + Enter saves, as in the app's
 * other long texts. `save` sends the text (the backend checks its length); on success the box
 * empties for the next note, or `onCancel` closes it when editing. */
export function NoteEditor({
  initial = "",
  submitLabel,
  busyLabel,
  save,
  onCancel,
}: {
  initial?: string
  submitLabel: string
  busyLabel: string
  save: (text: string) => Promise<void>
  // Editing a note: a Cancel button, and the box gets the focus at once.
  onCancel?: () => void
}) {
  const t = useTranslations("interviews")
  const common = useTranslations("common")
  const [text, setText] = useState(initial)
  const [busy, setBusy] = useState(false)

  function focusAtEnd(box: HTMLTextAreaElement | null) {
    if (!box || document.activeElement === box) {
      return
    }

    box.focus()
    box.setSelectionRange(box.value.length, box.value.length)
  }

  async function submit(event: FormEvent) {
    event.preventDefault()

    if (!text.trim() || busy) {
      return
    }

    setBusy(true)

    try {
      await save(text)
      setText("")
    } catch (error) {
      toast.error(
        serviceRefusal(error, [403, 404]) ??
          apiErrorMessage(error, t("noteFailed"))
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit}>
      <FloatingTextarea
        label={t("noteLabel")}
        placeholder={t("notePlaceholder")}
        value={text}
        maxLength={MAX_NOTE_LENGTH}
        dir="auto"
        // Editing a note: focused at once, the cursor at the note's end, not its start.
        ref={onCancel ? focusAtEnd : undefined}
        className="min-h-36"
        onChange={(event) => setText(event.target.value)}
        onKeyDown={(event) => {
          if (isSubmitShortcut(event)) {
            event.preventDefault()
            event.currentTarget.form?.requestSubmit()
          }

          if (event.key === "Escape" && onCancel) {
            onCancel()
          }
        }}
        hint={<SubmitHint />}
        action={
          <>
            {onCancel && (
              <Button
                type="button"
                variant="ghost"
                className="h-10 shrink-0 rounded-lg px-5 text-base"
                disabled={busy}
                onClick={onCancel}
              >
                {common("cancel")}
              </Button>
            )}
            <Button
              type="submit"
              className="h-10 shrink-0 rounded-lg px-5 text-base"
              disabled={busy || !text.trim()}
            >
              {busy ? busyLabel : submitLabel}
            </Button>
          </>
        }
      />
    </form>
  )
}
