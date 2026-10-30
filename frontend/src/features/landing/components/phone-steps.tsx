import { cn } from "cn"
import type { LucideIcon } from "lucide-react"

import { IconCard, PHONE_CARDS } from "@/features/landing/components/icon-card"

/** A section's steps as small grey cards, one under another, on phones only: there they stand
 * in for the section's animated picture, which shows from tablets up. */
export function PhoneSteps({
  steps,
  className,
}: {
  steps: { key: string; icon: LucideIcon; title: string; text: string }[]
  // The cards' fill, when not the site's grey (on a grey band, the page's own).
  className?: string
}) {
  return (
    <ul data-testid="phone-steps" className={cn("grid sm:hidden", PHONE_CARDS)}>
      {steps.map((step) => (
        <IconCard
          key={step.key}
          icon={step.icon}
          title={step.title}
          className={className}
        >
          {step.text}
        </IconCard>
      ))}
    </ul>
  )
}
