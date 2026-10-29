import { cn } from "cn"

import { AiPulse } from "@/components/common/ai-pulse"

/** What a page shows while its content loads, named for screen readers (`label`): prepza's
 * loading mark. `compact` for a part of a page, a dialog or a panel. */
export function LoadingSpinner({
  label,
  compact = false,
}: {
  label: string
  compact?: boolean
}) {
  return (
    <div
      className={cn("flex justify-center", compact ? "py-8" : "py-24")}
      role="status"
      data-testid="page-loading"
    >
      <AiPulse label={label} className={compact ? "size-10" : "size-14"} />
    </div>
  )
}
