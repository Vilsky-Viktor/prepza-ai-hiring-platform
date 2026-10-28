"use client"

import * as React from "react"
import { Dialog as DialogPrimitive } from "@base-ui/react/dialog"
import { cn } from "cn"
import { useTranslations } from "next-intl"

import { Button } from "@/components/ui/button"
import { XIcon } from "lucide-react"

function Dialog({ ...props }: DialogPrimitive.Root.Props) {
  return <DialogPrimitive.Root data-slot="dialog" {...props} />
}

function DialogTrigger({ ...props }: DialogPrimitive.Trigger.Props) {
  return <DialogPrimitive.Trigger data-slot="dialog-trigger" {...props} />
}

function DialogPortal({ ...props }: DialogPrimitive.Portal.Props) {
  return <DialogPrimitive.Portal data-slot="dialog-portal" {...props} />
}

function DialogClose({ ...props }: DialogPrimitive.Close.Props) {
  return <DialogPrimitive.Close data-slot="dialog-close" {...props} />
}

function DialogOverlay({
  className,
  ...props
}: DialogPrimitive.Backdrop.Props) {
  return (
    <DialogPrimitive.Backdrop
      data-slot="dialog-overlay"
      className={cn(
        "fixed inset-0 isolate z-50 bg-black/10 transition-opacity duration-200 ease-out data-[ending-style]:opacity-0 data-[ending-style]:duration-150 data-[starting-style]:opacity-0 supports-backdrop-filter:backdrop-blur-xs",
        className
      )}
      {...props}
    />
  )
}

// Open and close: the sheet slides in from its side (from the bottom on phones), a popup fades
// in rising a little and growing slightly; about 200 ms in and 150 ms out, eased. Reduced
// motion makes them instant (globals.css). Base UI keeps a closing popup mounted until its
// transition ends. On phones a popup spans the screen's width, with square corners. A popup taller
// than the screen scrolls its body only: its buttons (DialogFooter) sit under it, outside the
// scrolling, so the scrollbar never runs beside them.
const SHEET_CLASSES =
  "fixed inset-y-0 end-0 z-50 flex w-full flex-col bg-popover text-base text-popover-foreground ring-1 ring-foreground/10 outline-none transition-[translate] duration-200 ease-out sm:w-[var(--sheet-width,28rem)] data-[ending-style]:duration-150 data-[ending-style]:ease-in max-sm:data-[starting-style]:translate-y-full max-sm:data-[ending-style]:translate-y-full sm:data-[starting-style]:translate-x-full sm:data-[ending-style]:translate-x-full sm:rtl:data-[starting-style]:-translate-x-full sm:rtl:data-[ending-style]:-translate-x-full"
const POPUP_CLASSES =
  "fixed top-1/2 left-1/2 z-50 flex max-h-dvh w-full max-w-full -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden sm:rounded-xl bg-popover text-base text-popover-foreground ring-1 ring-foreground/10 outline-none transition-[opacity,translate,scale] duration-200 ease-out sm:max-w-sm data-[ending-style]:translate-y-[calc(-50%+10px)] data-[ending-style]:scale-[0.97] data-[ending-style]:opacity-0 data-[ending-style]:duration-150 data-[starting-style]:translate-y-[calc(-50%+10px)] data-[starting-style]:scale-[0.97] data-[starting-style]:opacity-0"

// A popup's body: its content, with the room around it, scrolling when it's taller than the popup.
const POPUP_BODY_CLASSES =
  "grid min-h-0 flex-1 gap-8 overflow-y-auto overscroll-contain px-10 pt-10 pb-10 max-sm:flex max-sm:flex-col"

function DialogContent({
  className,
  bodyClassName,
  children,
  showCloseButton = true,
  sheet = false,
  ...props
}: DialogPrimitive.Popup.Props & {
  // The body's own classes (its spacing), as `className` is the popup's (its size).
  bodyClassName?: string
  showCloseButton?: boolean
  // A panel along the end side, the whole screen on phones, with no backdrop: the page stays
  // usable beside it (open it with the Dialog's modal={false}); 28rem wide unless --sheet-width says.
  sheet?: boolean
}) {
  const t = useTranslations("common")
  // A popup's buttons go under its scrolling body; a sheet lays out its own content.
  const items = React.Children.toArray(children)
  const footers = sheet
    ? []
    : items.filter(
        (item) => React.isValidElement(item) && item.type === DialogFooter
      )
  const body = items.filter((item) => !footers.includes(item))

  return (
    <DialogPortal>
      {!sheet && <DialogOverlay />}
      <DialogPrimitive.Popup
        data-slot="dialog-content"
        className={cn(sheet ? SHEET_CLASSES : POPUP_CLASSES, className)}
        {...props}
      >
        {sheet ? (
          children
        ) : (
          <>
            <div className={cn(POPUP_BODY_CLASSES, bodyClassName)}>{body}</div>
            {footers.map((footer) =>
              React.cloneElement(
                footer as React.ReactElement<{ className?: string }>,
                {
                  className: cn(
                    (footer as React.ReactElement<{ className?: string }>).props
                      .className,
                    "static m-0"
                  ),
                }
              )
            )}
          </>
        )}
        {showCloseButton && (
          <DialogPrimitive.Close
            data-slot="dialog-close"
            render={
              <Button
                variant="ghost"
                className="absolute end-4 top-4"
                size="icon-sm"
              />
            }
          >
            <XIcon />
            <span className="sr-only">{t("close")}</span>
          </DialogPrimitive.Close>
        )}
      </DialogPrimitive.Popup>
    </DialogPortal>
  )
}

function DialogHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="dialog-header"
      // With a description under the title, more room between them, and between the lines.
      className={cn(
        "flex flex-col gap-2 has-data-[slot=dialog-description]:gap-4 has-data-[slot=dialog-description]:*:data-[slot=dialog-title]:mb-2",
        className
      )}
      {...props}
    />
  )
}

// A dialog's buttons, all one height and font: side by side and equal on phones, at the end
// from tablets up. Always in sight, at the dialog's bottom, however much of it scrolls above.
function DialogFooter({
  className,
  showCloseButton = false,
  children,
  ...props
}: React.ComponentProps<"div"> & {
  showCloseButton?: boolean
}) {
  const t = useTranslations("common")

  return (
    <div
      data-slot="dialog-footer"
      className={cn(
        "sticky -bottom-10 -mx-10 mt-auto -mb-10 flex shrink-0 gap-2 border-t bg-[color-mix(in_oklab,var(--color-muted)_50%,var(--color-popover))] px-4 py-3 *:h-10 *:px-5 *:text-base max-sm:*:flex-1 sm:justify-end sm:rounded-b-xl",
        className
      )}
      {...props}
    >
      {children}
      {showCloseButton && (
        <DialogPrimitive.Close
          render={<Button variant="outline" className="h-10 px-5 text-base" />}
        >
          {t("close")}
        </DialogPrimitive.Close>
      )}
    </div>
  )
}

function DialogTitle({ className, ...props }: DialogPrimitive.Title.Props) {
  return (
    <DialogPrimitive.Title
      data-slot="dialog-title"
      className={cn("font-heading text-xl leading-none font-medium", className)}
      {...props}
    />
  )
}

function DialogDescription({
  className,
  ...props
}: DialogPrimitive.Description.Props) {
  return (
    <DialogPrimitive.Description
      data-slot="dialog-description"
      className={cn(
        "text-base text-muted-foreground *:[a]:underline *:[a]:underline-offset-3 *:[a]:hover:text-foreground",
        className
      )}
      {...props}
    />
  )
}

export {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogOverlay,
  DialogPortal,
  DialogTitle,
  DialogTrigger,
}
