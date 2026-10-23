import { cn } from "cn"

import { AI_CHIP_MASK } from "@/constants/ai-mark"

/** prepza's loading mark: the AI chip from the landing's quality loop, lit like the "ask Mira"
 * button's border (a bright arc of the primary colour circling over a faint one, shown only
 * through the chip's lines), and a rounded-square ring pulsing out of it. With reduced motion,
 * the arc and the ring stand still. `className` sizes it (e.g. `size-14`); `label` names it for
 * screen readers, or it's hidden from them. */
export function AiPulse({
  className,
  label,
}: {
  className?: string
  label?: string
}) {
  return (
    <span
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      className={cn("relative flex shrink-0", className)}
    >
      <span className="absolute inset-0 animate-ping rounded-[28%] border-2 border-primary/50 [animation-duration:1.6s] motion-reduce:hidden" />
      {/* The chip, its lines filled with the circling arc (agent-border.css's angle and turn). */}
      <span
        className="absolute inset-0 animate-[agent-border_2.2s_linear_infinite]"
        style={{
          mask: `${AI_CHIP_MASK} center / contain no-repeat`,
          background:
            "conic-gradient(from var(--agent-angle), var(--primary), color-mix(in oklch, var(--primary) 25%, transparent) 25%, color-mix(in oklch, var(--primary) 25%, transparent) 75%, var(--primary))",
        }}
      />
    </span>
  )
}
