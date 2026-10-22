import { LoaderCircleIcon } from "lucide-react"

/** The spinner a page shows while its content loads, named for screen readers (`label`). */
export function LoadingSpinner({ label }: { label: string }) {
  return (
    <div className="flex justify-center py-24" role="status">
      <LoaderCircleIcon
        aria-label={label}
        className="size-8 animate-spin text-muted-foreground"
      />
    </div>
  )
}
