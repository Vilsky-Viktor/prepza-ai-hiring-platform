"use client"

import { cn } from "cn"
import { ArrowUpIcon, SquareIcon } from "lucide-react"
import { useTranslations } from "next-intl"

import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { isChatNewLine, isChatSend } from "@/lib/keys"

/** A chat's input row: a round text field with Send at its end; Enter sends and ⌘/Ctrl + Enter
 * adds a new line, as the small hint under it says (not on touch screens). While
 * an answer streams, Send is off, or is Stop when `onStop` is given. `children` sit before it
 * (the assistant's voice button). */
export function ChatInput({
  value,
  onChange,
  onSubmit,
  label,
  placeholder,
  maxLength,
  streaming,
  onStop,
  stopLabel,
  children,
  inputRef,
}: {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  label: string
  placeholder: string
  maxLength?: number
  streaming: boolean
  onStop?: () => void
  stopLabel?: string
  children?: React.ReactNode
  inputRef?: React.Ref<HTMLTextAreaElement>
}) {
  const common = useTranslations("common")

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (value.trim() && !streaming) {
      onSubmit()
    }
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    const field = event.currentTarget

    if (isChatSend(event)) {
      event.preventDefault()
      field.form?.requestSubmit()
    } else if (isChatNewLine(event)) {
      event.preventDefault()
      // The line break goes where the cursor is, replacing any selection.
      const { selectionStart, selectionEnd } = field
      const next = `${value.slice(0, selectionStart)}\n${value.slice(selectionEnd)}`

      if (maxLength === undefined || next.length <= maxLength) {
        onChange(next)
        requestAnimationFrame(() => {
          field.selectionStart = field.selectionEnd = selectionStart + 1
        })
      }
    }
  }

  return (
    <div>
      <form
        onSubmit={submit}
        className="relative rounded-[2rem] border border-transparent transition-colors focus-within:border-ring"
      >
        <Textarea
          ref={inputRef}
          maxLength={maxLength}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          aria-label={label}
          className={cn(
            "max-h-40 min-h-16 resize-none overscroll-contain rounded-xl border-0 bg-surface px-6 py-4 pe-20 text-lg shadow-none focus-visible:border-transparent focus-visible:ring-0 md:text-lg",
            children && "pe-32"
          )}
        />
        {/* The width of the field, so what the buttons show above it (the voice button's status)
          centers on it; clicks pass through to the field. */}
        <div className="pointer-events-none absolute inset-x-3 top-3 flex items-center justify-end gap-2 *:pointer-events-auto">
          {children}
          {streaming && onStop ? (
            <Button
              type="button"
              size="icon"
              className="size-10 rounded-lg"
              onClick={onStop}
              aria-label={stopLabel}
            >
              <SquareIcon className="size-4 fill-current" />
            </Button>
          ) : (
            <Button
              type="submit"
              size="icon"
              className="size-10 rounded-lg"
              disabled={!value.trim() || streaming}
              aria-label={common("send")}
            >
              <ArrowUpIcon className="size-5" />
            </Button>
          )}
        </div>
      </form>
      <p className="mt-2 text-center text-xs text-muted-foreground pointer-coarse:hidden">
        {common("chatKeysHint")}
      </p>
    </div>
  )
}
