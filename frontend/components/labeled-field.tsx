import { cn } from "cn"

/** A form field with its name always shown above it, as PillSelect's label is: a placeholder
 * alone vanishes once something is typed (WCAG 3.3.2). The label names the field, so the field
 * needs no aria-label of its own. With `htmlFor` (the field's id) the label points at it,
 * for a field that sits with buttons of its own (a send button in its corner). */
export function LabeledField({
  label,
  htmlFor,
  className,
  children,
}: {
  label: string
  htmlFor?: string
  className?: string
  children: React.ReactNode
}) {
  if (htmlFor) {
    return (
      <div className={cn("space-y-2", className)}>
        <label
          htmlFor={htmlFor}
          className="block text-sm text-muted-foreground"
        >
          {label}
        </label>
        {children}
      </div>
    )
  }

  return (
    <label className={cn("block space-y-2", className)}>
      <span className="block text-sm text-muted-foreground">{label}</span>
      {children}
    </label>
  )
}
