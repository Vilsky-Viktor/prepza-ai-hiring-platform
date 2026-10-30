"use client"

import { cn } from "cn"
import { type ComponentProps, type ReactNode, useId } from "react"

import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  FLOAT_ADORNMENT,
  FLOAT_BOX,
  FLOAT_FIELD,
  FLOAT_LABEL,
  FLOAT_LABEL_UP,
} from "@/config/floating-label"
import { adornmentRoom } from "@/lib/floating-field"

/** The site's grey field with its name: inside, where the value goes, while the field is empty,
 * and a small pill on its top edge once it's focused or filled (CSS alone, autofill too). The
 * field fills the box, so a click anywhere in it focuses the field; the name is its <label>.
 * `prefix` and `suffix` are a sign or unit inside the box ("$", "px"); `action` is a button at
 * its end ("Add"), and the name then rests at the field's start. `boxClassName` sizes the box (a
 * width); `className` goes to the field. */
export function FloatingInput({
  label,
  prefix,
  suffix,
  action,
  boxClassName,
  className,
  style,
  id,
  placeholder,
  type,
  ...props
}: Omit<ComponentProps<"input">, "prefix"> & {
  label: string
  prefix?: string
  suffix?: string
  action?: ReactNode
  boxClassName?: string
}) {
  const own = useId()
  const fieldId = id ?? own

  return (
    <div
      className={cn(
        FLOAT_BOX,
        action && "flex items-center gap-2 pe-2",
        boxClassName
      )}
    >
      <Input
        {...props}
        id={fieldId}
        type={type}
        // A space when there's no hint: `:placeholder-shown` then tells an empty field.
        placeholder={placeholder ?? " "}
        className={cn(FLOAT_FIELD, "h-13.5", action && "min-w-0", className)}
        // Room for the sign or unit, by its length.
        style={{
          paddingInlineStart: adornmentRoom(prefix),
          paddingInlineEnd: adornmentRoom(suffix),
          ...style,
        }}
      />
      {prefix && (
        <span aria-hidden className={cn(FLOAT_ADORNMENT, "start-6")}>
          {prefix}
        </span>
      )}
      {suffix && (
        <span aria-hidden className={cn(FLOAT_ADORNMENT, "end-6")}>
          {suffix}
        </span>
      )}
      {action}
      <label htmlFor={fieldId} className={cn(FLOAT_LABEL, FLOAT_LABEL_UP)}>
        {label}
      </label>
    </div>
  )
}

/** FloatingInput for a textarea: the name rests on the first line. `hint` (the send shortcut)
 * and `action` (a button or a few: "Post") share the box's bottom row, the hint at its start and
 * the buttons at its end, as the home page's description box has them, the text kept clear of
 * that row; with `action`, the name rests at the field's start, as FloatingInput's does. */
export function FloatingTextarea({
  label,
  action,
  hint,
  boxClassName,
  className,
  id,
  placeholder,
  ...props
}: ComponentProps<"textarea"> & {
  label: string
  action?: ReactNode
  hint?: ReactNode
  boxClassName?: string
}) {
  const own = useId()
  const fieldId = id ?? own

  return (
    <div className={cn(FLOAT_BOX, boxClassName)}>
      <Textarea
        {...props}
        id={fieldId}
        placeholder={placeholder ?? " "}
        className={cn(
          FLOAT_FIELD,
          "min-h-32 resize-none py-4",
          (hint || action) && "pb-16",
          className
        )}
      />
      {(hint || action) && (
        <div className="pointer-events-none absolute inset-x-0 bottom-0 flex items-center justify-between gap-4 ps-6 pe-3 pb-3">
          {hint}
          {action && (
            <div className="pointer-events-auto ms-auto flex items-center gap-2">
              {action}
            </div>
          )}
        </div>
      )}
      <label htmlFor={fieldId} className={cn(FLOAT_LABEL, FLOAT_LABEL_UP)}>
        {label}
      </label>
    </div>
  )
}
