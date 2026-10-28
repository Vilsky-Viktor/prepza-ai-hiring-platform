"use client"

import { useTranslations } from "next-intl"

import { LoadingSpinner } from "@/components/common/loading-spinner"
import { Button } from "@/components/ui/button"
import type { LinkStatus as Status } from "@/hooks/use-link-data"

/** A link's page while it isn't there: a spinner while loading, `invalid` when the link is gone,
 * and a way to try again when it couldn't be loaded. */
export function LinkStatus({
  status,
  invalid,
  onRetry,
}: {
  status: Exclude<Status, "ready">
  invalid: string
  onRetry: () => void
}) {
  const common = useTranslations("common")

  if (status === "loading") {
    return <LoadingSpinner label={common("loading")} />
  }

  if (status === "missing") {
    return (
      <p
        data-testid="link-invalid"
        className="py-24 text-center text-base text-muted-foreground"
      >
        {invalid}
      </p>
    )
  }

  return (
    <div data-testid="link-failed" className="space-y-4 py-24 text-center">
      <p className="text-base text-muted-foreground">{common("failed")}</p>
      <Button
        variant="outline"
        className="h-10 px-5 text-base"
        onClick={onRetry}
      >
        {common("retry")}
      </Button>
    </div>
  )
}
