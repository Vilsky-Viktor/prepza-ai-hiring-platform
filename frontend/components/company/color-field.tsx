"use client"

import { useState } from "react"

import { Input } from "@/components/ui/input"
import { HEX_COLOR } from "@/constants/brand"

/** One color: its swatch opens the system's color picker, and its hex code can be typed;
 * a code counts once it's whole ("#1a2b3c"). */
export function ColorField({
  label,
  value,
  onChange,
}: {
  label: string
  value: string
  onChange: (value: string) => void
}) {
  const [typed, setTyped] = useState<string | null>(null)

  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="flex items-center gap-2">
        <input
          type="color"
          value={value}
          onChange={(event) => {
            setTyped(null)
            onChange(event.target.value)
          }}
          className="size-8 shrink-0 cursor-pointer appearance-none rounded-full border bg-transparent p-0 [&::-moz-color-swatch]:rounded-full [&::-moz-color-swatch]:border-0 [&::-webkit-color-swatch]:rounded-full [&::-webkit-color-swatch]:border-0 [&::-webkit-color-swatch-wrapper]:p-0"
          aria-label={label}
        />
        <Input
          value={typed ?? value}
          maxLength={7}
          spellCheck={false}
          // A hex code reads left to right on every page.
          dir="ltr"
          className="w-28 border-transparent font-mono"
          aria-label={label}
          onChange={(event) => {
            const next = event.target.value.trim()
            setTyped(next)

            if (HEX_COLOR.test(next)) {
              onChange(next.toLowerCase())
            }
          }}
          onBlur={() => setTyped(null)}
        />
      </span>
    </label>
  )
}
