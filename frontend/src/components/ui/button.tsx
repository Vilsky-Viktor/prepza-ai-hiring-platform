import { Button as ButtonPrimitive } from "@base-ui/react/button"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "cn"
import type { ReactNode } from "react"

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"

// Pressed, a button shrinks and dims a little: on a phone, with no hover, that's the sign a tap
// landed.
const buttonVariants = cva(
  "group/button inline-flex shrink-0 items-center justify-center rounded-[var(--button-radius,var(--radius-xl))] border border-transparent bg-clip-padding text-sm font-normal whitespace-nowrap lowercase transition-all outline-none select-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 active:scale-[0.97] active:opacity-80 active:not-aria-[haspopup]:translate-y-px disabled:pointer-events-none disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        // Trying: the primary fill, a touch lighter at the top, with a faint light line along its
        // top inside edge, so it reads as slightly raised; a touch brighter on hover. The gradient
        // look it replaces:
        // "bg-primary-gradient text-primary-foreground transition-[filter] hover:brightness-110".
        default:
          "bg-primary bg-[linear-gradient(to_bottom,color-mix(in_oklch,var(--primary)_88%,white),var(--primary))] text-primary-foreground shadow-[inset_0_1px_0_rgb(255_255_255/0.25)] transition-[filter] hover:brightness-110 aria-expanded:brightness-110",
        outline:
          "border-border bg-transparent hover:bg-surface hover:text-foreground aria-expanded:bg-surface aria-expanded:text-foreground dark:border-input",
        // The site's grey with the primary's light top line, fainter; a step lighter on hover.
        secondary:
          "bg-surface text-secondary-foreground shadow-[inset_0_1px_0_rgb(255_255_255/0.6)] hover:bg-[color-mix(in_oklch,var(--surface),var(--foreground)_5%)] aria-expanded:bg-surface aria-expanded:text-secondary-foreground dark:shadow-[inset_0_1px_0_rgb(255_255_255/0.06)]",
        ghost:
          "hover:bg-surface hover:text-foreground active:bg-surface aria-expanded:bg-surface aria-expanded:text-foreground",
        destructive:
          "bg-destructive/10 text-destructive hover:bg-destructive/20 focus-visible:border-destructive/40 focus-visible:ring-destructive/20 dark:bg-destructive/20 dark:hover:bg-destructive/30 dark:focus-visible:ring-destructive/40",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default:
          "h-8 gap-1.5 px-2.5 has-data-[icon=inline-end]:pe-2 has-data-[icon=inline-start]:ps-2",
        xs: "h-6 gap-1 px-2 text-xs gradient-soft in-data-[slot=button-group]:rounded-lg has-data-[icon=inline-end]:pe-1.5 has-data-[icon=inline-start]:ps-1.5 [&_svg:not([class*='size-'])]:size-3",
        sm: "h-7 gap-1 px-2.5 text-[0.8rem] gradient-soft in-data-[slot=button-group]:rounded-lg has-data-[icon=inline-end]:pe-1.5 has-data-[icon=inline-start]:ps-1.5 [&_svg:not([class*='size-'])]:size-3.5",
        lg: "h-9 gap-1.5 px-2.5 has-data-[icon=inline-end]:pe-2 has-data-[icon=inline-start]:ps-2",
        icon: "size-8 gradient-soft",
        "icon-xs":
          "size-6 gradient-soft in-data-[slot=button-group]:rounded-lg [&_svg:not([class*='size-'])]:size-3",
        "icon-sm":
          "size-7 gradient-soft in-data-[slot=button-group]:rounded-lg",
        "icon-lg": "size-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  tooltip,
  ...props
}: ButtonPrimitive.Props &
  VariantProps<typeof buttonVariants> & {
    // Shown on hover; an icon-only button shows its aria-label when this isn't given.
    tooltip?: ReactNode
  }) {
  const button = (
    <ButtonPrimitive
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      // Rendered as something else than a <button> (`nativeButton={false}`), it's always a link
      // here: it stays a link to assistive tech, not the button role Base UI gives it.
      {...(props.nativeButton === false && { role: "link" })}
      {...props}
    />
  )
  const tip =
    tooltip ?? (size?.startsWith("icon") ? props["aria-label"] : undefined)

  if (!tip) {
    return button
  }

  return (
    <Tooltip>
      <TooltipTrigger render={button} />
      <TooltipContent>{tip}</TooltipContent>
    </Tooltip>
  )
}

export { Button, buttonVariants }
