import { AiPulse } from "@/components/ai-pulse"

/** What a page shows while its content loads, named for screen readers (`label`): prepza's
 * loading mark. */
export function LoadingSpinner({ label }: { label: string }) {
  return (
    <div
      className="flex justify-center py-24"
      role="status"
      data-testid="page-loading"
    >
      <AiPulse label={label} className="size-14" />
    </div>
  )
}
