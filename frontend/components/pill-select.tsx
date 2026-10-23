import type { ReactNode } from "react"

import { MenuPill } from "@/components/menu-pill"

/** The site's select, with an optional label inside it (as the site's fields have theirs): the
 * pill opens the site's menu, never the browser's own list. */
export function PillSelect({
  label,
  ariaLabel,
  value,
  options,
  onChange,
  placeholder,
  disabled,
  className,
  pillClassName,
}: {
  // Shown inside the select; without it, `ariaLabel` names it.
  label?: string
  ariaLabel?: string
  // Null until something is chosen, showing `placeholder`.
  value: string | null
  // `note`: a line under the option in the open menu; `display`: what the pill shows once
  // it's chosen, instead of the label.
  options: {
    value: string
    label: string
    note?: string
    fontFamily?: string
    lang?: string
    display?: ReactNode
  }[]
  onChange: (value: string) => void
  placeholder?: string
  disabled?: boolean
  className?: string
  // The pill's own classes: a width that stays as the choice changes, say.
  pillClassName?: string
}) {
  return (
    <div className={className}>
      <MenuPill
        label={label}
        ariaLabel={ariaLabel}
        value={value}
        options={options.map((option) => ({ ...option, keepCase: true }))}
        onChange={onChange}
        placeholder={placeholder}
        disabled={disabled}
        className={pillClassName}
      />
    </div>
  )
}
