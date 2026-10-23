import { cn } from "cn"
import { CircleCheckIcon } from "lucide-react"

import { Caret } from "@/components/landing/caret"

/** A dialog, small, over the whole panel (whose box must be `relative`) while `open`: the
 * panel dimmed and the dialog's card in its middle. */
export function DemoPopup({
  open,
  children,
}: {
  open: boolean
  children: React.ReactNode
}) {
  return (
    <div
      className={cn(
        "absolute inset-0 z-5 flex items-center justify-center rounded-xl bg-black/10 p-3 transition-opacity duration-200",
        !open && "invisible opacity-0"
      )}
    >
      <div
        className={cn(
          "w-full max-w-md space-y-5 rounded-xl bg-popover p-5 text-base text-popover-foreground ring-1 ring-foreground/10 transition-[translate,scale] duration-200 sm:p-6",
          !open && "translate-y-2.5 scale-[0.97]"
        )}
      >
        {children}
      </div>
    </div>
  )
}

/** A popup's email field: `email` as typed so far, a caret while `typing`, else `placeholder`;
 * `ref` for the pointer. */
export function DemoEmailField({
  ref,
  email,
  typing,
  placeholder,
}: {
  ref: React.Ref<HTMLDivElement>
  email: string
  typing: boolean
  placeholder: string
}) {
  return (
    <div
      ref={ref}
      className={cn(
        "flex h-12 items-center rounded-xl border bg-surface px-5",
        typing || email ? "border-ring" : "border-input"
      )}
    >
      {email || typing ? (
        <>
          <span className="truncate">{email}</span>
          {typing && <Caret />}
        </>
      ) : (
        <span className="truncate text-muted-foreground">{placeholder}</span>
      )}
    </div>
  )
}

/** The notice the site shows once something is sent, `text`, at the panel's bottom while
 * `shown`. */
export function DemoSentNotice({
  shown,
  text,
}: {
  shown: boolean
  text: React.ReactNode
}) {
  return (
    <div
      data-testid="demo-sent"
      data-shown={shown}
      className={cn(
        "absolute inset-x-3 bottom-4 z-5 flex justify-center transition-[opacity,translate] duration-300",
        !shown && "invisible translate-y-2 opacity-0"
      )}
    >
      <p className="flex items-center gap-3 rounded-xl border bg-popover px-4 py-3 text-base text-popover-foreground">
        <CircleCheckIcon className="size-6 shrink-0" />
        <span className="min-w-0">{text}</span>
      </p>
    </div>
  )
}
