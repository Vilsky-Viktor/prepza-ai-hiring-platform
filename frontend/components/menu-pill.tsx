"use client"

import { cn } from "cn"
import { ChevronDownIcon } from "lucide-react"
import { type ReactNode, useId } from "react"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { MENU_PILL_CHEVRON_CLASS, MENU_PILL_CLASS } from "@/constants/menu-pill"
import { languageOf } from "@/lib/locale"

/** The site's select pill (as components/pill-select.tsx looks) opening the site's menu, not the
 * browser's: one choice among `options`, each with an optional line under it. Shows
 * `placeholder` until something is chosen. Labels are lowercase like the site's; `keepCase` keeps
 * a name's capitals (an ATS job, an interview's title); `fontFamily` draws one in a font; `lang`
 * marks one written in another language (a language's own name). */
export function MenuPill({
  ariaLabel,
  value,
  options,
  onChange,
  placeholder,
  disabled,
  className,
}: {
  ariaLabel: string
  value: string | null
  options: {
    value: string
    label: string
    note?: string
    keepCase?: boolean
    // Draws the label in this font: a font's name in itself.
    fontFamily?: string
    lang?: string
    // A link instead of a choice: the option opens this address (another language's page).
    // Shown in the pill instead of the label once chosen.
    display?: ReactNode
  }[]
  onChange: (value: string) => void
  placeholder?: string
  disabled?: boolean
  className?: string
}) {
  const chosen = options.find((option) => option.value === value)
  // Named by its label and what it shows, so the visible text is in its name (WCAG 2.5.3).
  const labelId = useId()
  const valueId = useId()

  // In a div of its own: the open menu adds a hidden element beside its button, which a parent's
  // spacing (space-y) would push the content below it down for.
  return (
    <div>
      <DropdownMenu>
        <DropdownMenuTrigger
          disabled={disabled}
          aria-labelledby={`${labelId} ${valueId}`}
          className={cn(
            MENU_PILL_CLASS,
            !chosen && "text-muted-foreground",
            className
          )}
        >
          <span id={labelId} className="sr-only">
            {ariaLabel}
          </span>
          <span
            id={valueId}
            className={cn("truncate", chosen?.keepCase && "normal-case")}
            style={{ fontFamily: chosen?.fontFamily }}
            {...languageOf(chosen?.lang)}
          >
            {chosen ? (chosen.display ?? chosen.label) : placeholder}
          </span>
          <ChevronDownIcon aria-hidden className={MENU_PILL_CHEVRON_CLASS} />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="max-h-80 w-72 p-2">
          <DropdownMenuRadioGroup value={value ?? ""} onValueChange={onChange}>
            {options.map((option) => (
              <DropdownMenuRadioItem
                key={option.value}
                value={option.value}
                className="items-start px-3 py-2"
              >
                <span className="space-y-0.5">
                  <span
                    className={cn(
                      "block",
                      option.keepCase ? "normal-case" : "lowercase"
                    )}
                    style={{ fontFamily: option.fontFamily }}
                    {...languageOf(option.lang)}
                  >
                    {option.label}
                  </span>
                  {option.note && (
                    <span className="block text-sm text-muted-foreground">
                      {option.note}
                    </span>
                  )}
                </span>
              </DropdownMenuRadioItem>
            ))}
          </DropdownMenuRadioGroup>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
