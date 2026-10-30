"use client"

import { cn } from "cn"
import { SquarePenIcon } from "lucide-react"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { type ReactNode, useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { MAX_TITLE_LENGTH } from "@/config/limits"
import { apiErrorMessage, apiFetch, serviceRefusal } from "@/lib/api"

const titleClass =
  "font-heading text-3xl font-medium tracking-tight text-balance normal-case"
// A secondary line under a title, such as a candidate's name under their email.
const smallClass = "text-sm text-muted-foreground break-all"

/** A page's title, edited in place: `path` takes {[field]: value}, {"title"} by default.
 * `maxLength` defaults to a test's title limit (a company's name is shorter). Not `editable`
 * (a viewer), it's a plain title. `hint` shows under the field while editing. `small` makes it
 * a secondary line under the title. With `emptyLabel` (text, or a node such as one with a
 * tooltip), it may be left blank (saved as blank)
 * and shows the label while it is. `label` names the field for screen readers, and `editLabel`
 * the pencil button after the text ("Edit title" by default), which starts editing too. `after`
 * (an icon) follows the last word, wrapping with it. */
export function EditableTitle({
  title,
  path,
  maxLength = MAX_TITLE_LENGTH,
  editable = true,
  hint,
  field = "title",
  label,
  small = false,
  emptyLabel,
  editLabel,
  after,
}: {
  title: string
  path: string
  maxLength?: number
  editable?: boolean
  hint?: string
  field?: string
  label?: string
  small?: boolean
  emptyLabel?: ReactNode
  editLabel?: string
  after?: ReactNode
}) {
  const t = useTranslations("common")
  const textClass = small ? smallClass : titleClass
  const Tag = small ? "p" : "h1"
  const shown: ReactNode = title || emptyLabel
  const router = useRouter()
  const inputRef = useRef<HTMLInputElement>(null)
  const skipSave = useRef(false)
  const savingRef = useRef(false)
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState(title)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!editing) {
      return
    }

    const input = inputRef.current

    if (!input) {
      return
    }

    const end = input.value.length

    input.focus()
    input.setSelectionRange(end, end)
  }, [editing])

  async function save() {
    const next = value.trim()

    if (savingRef.current) {
      return
    }

    if ((!next && emptyLabel === undefined) || next === title) {
      setValue(title)
      setEditing(false)

      return
    }

    savingRef.current = true
    setSaving(true)

    try {
      await apiFetch(path, {
        method: "PATCH",
        body: JSON.stringify({ [field]: next }),
      })
      setEditing(false)
      router.refresh()
    } catch (error) {
      // Says why, e.g. when another company already has the name.
      toast.error(
        serviceRefusal(error, [409]) ?? apiErrorMessage(error, t("titleFailed"))
      )
    } finally {
      savingRef.current = false
      setSaving(false)
    }
  }

  function cancel() {
    skipSave.current = true
    setValue(title)
    setEditing(false)
  }

  if (!editable) {
    return (
      <Tag className={textClass}>
        {/* The word joiner keeps `after` on the last word's line. */}
        {shown}
        {"\u2060"}
        {after}
      </Tag>
    )
  }

  function startEditing() {
    setValue(title)
    setEditing(true)
  }

  if (!editing) {
    const edit = editLabel ?? t("editTitle")
    // A title's last word goes in one unbreakable piece with its dot and the pencil, so they
    // wrap together.
    // A title is text: its last word is split off to wrap with the dot and the pencil.
    const split = title.lastIndexOf(" ")
    const head = title.slice(0, split + 1)
    const last = title.slice(split + 1)
    const pencil = (
      <EditPencil small={small} label={edit} onClick={startEditing} />
    )

    // Clicking the text edits too; the pencil is the button for the keyboard and screen
    // readers. A title draws its blue dot itself (.no-dot), so the pencil can sit over it.
    return (
      <Tag className={cn(textClass, !small && "no-dot")}>
        {/* A name or a title takes the direction of its own text, whatever the page's. */}
        <span
          dir="auto"
          className="cursor-text normal-case"
          onClick={startEditing}
        >
          {small ? (
            // A name can be one long word: it breaks, the word joiner keeps the pencil on.
            <>
              {shown}
              {"\u2060"}
              {pencil}
            </>
          ) : (
            <>
              {head}
              <span className="whitespace-nowrap">
                {last}
                <span className="inline-block w-[0.4em] text-start text-primary">
                  .
                </span>
                {pencil}
                {after}
              </span>
            </>
          )}
        </span>
      </Tag>
    )
  }

  const input = (
    <input
      ref={inputRef}
      // A name or a title takes its own direction as it's typed.
      dir="auto"
      maxLength={maxLength}
      aria-label={label ?? t("title")}
      disabled={saving}
      value={value}
      className={`${textClass} w-full min-w-0 rounded-xl border border-ring bg-transparent px-4 py-1 outline-none`}
      onChange={(event) => setValue(event.target.value)}
      onBlur={() => {
        if (skipSave.current) {
          skipSave.current = false

          return
        }

        void save()
      }}
      onKeyDown={(event) => {
        if (event.key === "Enter") {
          event.preventDefault()
          event.currentTarget.blur()
        }

        if (event.key === "Escape") {
          event.preventDefault()
          cancel()
        }
      }}
    />
  )

  if (!hint) {
    return input
  }

  return (
    <div className="space-y-1">
      {input}
      <p className="px-4 text-sm text-muted-foreground">{hint}</p>
    </div>
  )
}

/** The pencil after a title that starts editing it. On a name line, the app's small icon
 * button; over a title's dot, a bare pencil as wide as the dot's box and starting where it
 * does, its tip over the dot, raised clear of it like a superscript. */
function EditPencil({
  small,
  label,
  onClick,
}: {
  small: boolean
  label: string
  onClick: () => void
}) {
  if (small) {
    return (
      <Button
        type="button"
        variant="ghost"
        size="icon-xs"
        className="-my-1 ms-1 align-middle text-muted-foreground hover:text-foreground"
        aria-label={label}
        onClick={onClick}
      >
        <SquarePenIcon className="size-3.5" />
      </Button>
    )
  }

  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <button
            type="button"
            aria-label={label}
            className="-ms-[0.3em] inline-flex size-[0.55em] align-[0.3em] text-muted-foreground transition-colors hover:text-foreground"
            onClick={onClick}
          />
        }
      >
        <SquarePenIcon className="size-full rtl:-scale-x-100" />
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  )
}
