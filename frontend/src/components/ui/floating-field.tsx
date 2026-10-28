"use client"

import { cn } from "cn"
import { type ComponentProps, useId } from "react"

import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  FLOAT_ADORNMENT,
  FLOAT_ADORNMENT_PEER_SHOWN,
  FLOAT_BOX,
  FLOAT_FIELD,
  FLOAT_LABEL,
  FLOAT_LABEL_PEER_UP,
  FLOAT_LABEL_REST,
  FLOAT_LABEL_REST_TOP,
  FLOAT_LABEL_UP,
} from "@/constants/floating-label"
import { adornmentRoom, alwaysFilled } from "@/lib/floating-field"

/** The site's grey field with its name: inside, where the value goes, while the field is empty,
 * and a small pill on its top edge once it's focused or filled (CSS alone, autofill too). The
 * field fills the box, so a click anywhere in it focuses the field; the name is its <label>.
 * `prefix` and `suffix` are a sign or unit inside the box ("$", "px"). `boxClassName` sizes the
 * box (a width); `className` goes to the field. */
export function FloatingInput({
  label,
  prefix,
  suffix,
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
  boxClassName?: string
}) {
  const own = useId()
  const fieldId = id ?? own
  const filled = alwaysFilled(type)
  const adornment = cn(FLOAT_ADORNMENT, !filled && FLOAT_ADORNMENT_PEER_SHOWN)

  return (
    <div className={cn(FLOAT_BOX, boxClassName)}>
      <Input
        {...props}
        id={fieldId}
        type={type}
        // A space when there's no hint: `:placeholder-shown` then tells an empty field.
        placeholder={placeholder ?? " "}
        className={cn(FLOAT_FIELD, "h-13.5", className)}
        // Room for the sign or unit, by its length.
        style={{
          paddingInlineStart: adornmentRoom(prefix),
          paddingInlineEnd: adornmentRoom(suffix),
          ...style,
        }}
      />
      {prefix && (
        <span aria-hidden className={cn(adornment, "start-6")}>
          {prefix}
        </span>
      )}
      {suffix && (
        <span aria-hidden className={cn(adornment, "end-6")}>
          {suffix}
        </span>
      )}
      <label
        htmlFor={fieldId}
        className={cn(
          FLOAT_LABEL,
          filled ? FLOAT_LABEL_UP : [FLOAT_LABEL_REST, FLOAT_LABEL_PEER_UP]
        )}
      >
        {label}
      </label>
    </div>
  )
}

/** FloatingInput for a textarea: the name rests on the first line. */
export function FloatingTextarea({
  label,
  boxClassName,
  className,
  id,
  placeholder,
  ...props
}: ComponentProps<"textarea"> & { label: string; boxClassName?: string }) {
  const own = useId()
  const fieldId = id ?? own

  return (
    <div className={cn(FLOAT_BOX, boxClassName)}>
      <Textarea
        {...props}
        id={fieldId}
        placeholder={placeholder ?? " "}
        className={cn(FLOAT_FIELD, "min-h-32 resize-none py-4", className)}
      />
      <label
        htmlFor={fieldId}
        className={cn(FLOAT_LABEL, FLOAT_LABEL_REST_TOP, FLOAT_LABEL_PEER_UP)}
      >
        {label}
      </label>
    </div>
  )
}
