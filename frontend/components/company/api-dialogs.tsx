"use client"

import { Trash2Icon } from "lucide-react"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useState } from "react"
import { toast } from "sonner"

import { ConfirmDialog } from "@/components/confirm-dialog"
import { CopyValue } from "@/components/copy-field"
import { KeepAcronyms } from "@/components/keep-acronyms"
import { FloatingInput } from "@/components/ui/floating-field"
import { PillSelect } from "@/components/pill-select"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { WarningCard } from "@/components/warning-card"
import { apiErrorMessage, apiFetch } from "@/lib/api"

/** Making a key or a web hook: one field (and a key's expiry and permissions), then what the API
 * made, shown this once to copy. */
export function CreateDialog({
  path,
  field,
  maxLength,
  type = "text",
  label,
  placeholder,
  title,
  failed,
  shown,
  choice,
  ticks,
}: {
  // The /manage route that makes it, and the field it takes.
  path: string
  field: string
  maxLength: number
  type?: string
  // The trigger's and the submit button's text, the dialog's title, the field's name and hint.
  label: string
  placeholder: string
  title: string
  failed: string
  // What's shown once it's made: which of the answer's values, and the texts around it.
  shown: {
    value: string
    title: string
    text: string
    copy: string
    copied: string
  }
  // A second field to pick from, if any (a key's expiry): its name in the body, what it asks
  // (shown until something is picked) and its options; nothing is picked at first.
  choice?: {
    field: string
    label: string
    options: { value: string; label: string }[]
    // An option with a warning under the select while it's picked (a key that never expires).
    warning?: { value: string; text: string }
  }
  // Checkboxes to tick, if any (a key's permissions): their name in the body, what's ticked at
  // first, and the checkboxes themselves; at least one must be ticked.
  ticks?: {
    field: string
    initial: string[]
    render: (
      ticked: string[],
      onChange: (ticked: string[]) => void
    ) => React.ReactNode
  }
}) {
  const common = useTranslations("common")
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [value, setValue] = useState("")
  const [picked, setPicked] = useState<string | null>(null)
  const [ticked, setTicked] = useState(ticks?.initial ?? [])
  const [saving, setSaving] = useState(false)
  const [created, setCreated] = useState<string | null>(null)

  async function create(event: React.FormEvent) {
    event.preventDefault()
    setSaving(true)

    try {
      const answer = await apiFetch<Record<string, string>>(path, {
        method: "POST",
        body: JSON.stringify({
          [field]: value,
          ...(choice ? { [choice.field]: picked } : {}),
          ...(ticks ? { [ticks.field]: ticked } : {}),
        }),
      })
      setCreated(answer[shown.value])
      router.refresh()
    } catch (error) {
      toast.error(apiErrorMessage(error, failed))
    } finally {
      setSaving(false)
    }
  }

  function changeOpen(next: boolean) {
    if (saving) {
      return
    }

    setOpen(next)

    if (!next) {
      setValue("")
      setPicked(null)
      setTicked(ticks?.initial ?? [])
      setCreated(null)
    }
  }

  return (
    <Dialog open={open} onOpenChange={changeOpen}>
      <DialogTrigger
        render={<Button className="h-10 shrink-0 px-5 text-base" />}
      >
        {label}
      </DialogTrigger>
      <DialogContent showCloseButton={false} className="sm:max-w-xl">
        {created ? (
          <>
            <DialogHeader>
              <DialogTitle>{shown.title}</DialogTitle>
              <DialogDescription>{shown.text}</DialogDescription>
            </DialogHeader>
            <CopyValue
              value={created}
              label={shown.copy}
              copied={shown.copied}
            />
            <DialogFooter>
              <DialogClose render={<Button className="h-10 px-5 text-base" />}>
                {common("close")}
              </DialogClose>
            </DialogFooter>
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle>
                <KeepAcronyms text={title} />
              </DialogTitle>
            </DialogHeader>
            <form
              id={`create-${field}`}
              onSubmit={create}
              className="space-y-3"
            >
              <FloatingInput
                label={placeholder}
                required
                type={type}
                autoComplete="off"
                maxLength={maxLength}
                value={value}
                onChange={(event) => setValue(event.target.value)}
              />
              {choice && (
                <PillSelect
                  label={choice.label}
                  placeholder={choice.label}
                  value={picked}
                  options={choice.options}
                  onChange={setPicked}
                />
              )}
              {choice?.warning && picked === choice.warning.value && (
                <WarningCard>{choice.warning.text}</WarningCard>
              )}
              {ticks?.render(ticked, setTicked)}
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
                form={`create-${field}`}
                className="h-10 px-5 text-base"
                disabled={
                  saving ||
                  !value.trim() ||
                  (!!choice && !picked) ||
                  (!!ticks && !ticked.length)
                }
              >
                {label}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}

/** The bin icon, like removing a member, asking first; `path` is the /manage route to delete. */
export function RemoveButton({
  path,
  label,
  title,
  text,
  failed,
}: {
  path: string
  label: string
  title: string
  text: React.ReactNode
  failed: string
}) {
  const common = useTranslations("common")
  const router = useRouter()
  const [confirming, setConfirming] = useState(false)
  const [busy, setBusy] = useState(false)

  async function remove() {
    setBusy(true)

    try {
      await apiFetch(path, { method: "DELETE" })
      setConfirming(false)
      router.refresh()
    } catch (error) {
      toast.error(apiErrorMessage(error, failed))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <Button
        variant="ghost"
        size="icon"
        className="size-12 shrink-0 text-muted-foreground hover:text-destructive"
        aria-label={label}
        disabled={busy}
        onClick={() => setConfirming(true)}
      >
        <Trash2Icon className="size-6" />
      </Button>
      <ConfirmDialog
        open={confirming}
        onOpenChange={setConfirming}
        title={title}
        text={text}
        confirm={common("delete")}
        busy={busy}
        onConfirm={remove}
      />
    </>
  )
}
