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
import {
  FLOAT_LABEL,
  FLOAT_LABEL_REST,
  FLOAT_LABEL_UP,
} from "@/constants/floating-label"
import { MENU_PILL_CHEVRON_CLASS, MENU_PILL_CLASS } from "@/constants/menu-pill"
import { languageOf } from "@/lib/locale"

/** The site's select pill (as components/pill-select.tsx looks) opening the site's menu, not the
 * browser's: one choice among `options`, each with an optional line under it. Shows
 * `placeholder` until something is chosen. Labels are lowercase like the site's; `keepCase` keeps
 * a name's capitals (an ATS job, an interview's title); `fontFamily` draws one in a font; `lang`
 * marks one written in another language (a language's own name). With `label`, the pill shows
 * its name as the site's fields do (ui/floating-field.tsx): where the choice goes until something
 * is chosen, then a small pill on its top edge; `placeholder` isn't shown then. */
export function MenuPill({
  label,
  ariaLabel,
  value,
  options,
  onChange,
  placeholder,
  disabled,
  className,
}: {
  label?: string
  ariaLabel?: string
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
            !chosen && "text-placeholder",
            // Room for the raised label above it.
            label && "mt-3",
            className
          )}
        >
          <span
            id={labelId}
            className={
              label
                ? cn(
                    FLOAT_LABEL,
                    "max-w-[calc(100%-5rem)]",
                    chosen ? FLOAT_LABEL_UP : FLOAT_LABEL_REST
                  )
                : "sr-only"
            }
          >
            {label ?? ariaLabel}
          </span>
          {/* A space from the choice, so the visible text matches the button's name (WCAG 2.5.3). */}{" "}
          <span
            id={valueId}
            className={cn("truncate", chosen?.keepCase && "normal-case")}
            style={{ fontFamily: chosen?.fontFamily }}
            {...languageOf(chosen?.lang)}
          >
            {chosen ? (chosen.display ?? chosen.label) : !label && placeholder}
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
