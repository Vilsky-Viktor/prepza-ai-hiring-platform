"use client"

import * as Sentry from "@sentry/nextjs"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { startTransition, useEffect } from "react"

import { ReportProblem } from "@/components/report-problem"
import { Button } from "@/components/ui/button"

/** A page that failed: what happened, Retry (the page's data read again, then shown) and the way
 * home, and a way to report it; the error goes to Sentry. global-error.tsx shows it too, when the
 * root layout itself failed. */
export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const t = useTranslations("errors")
  const common = useTranslations("common")
  const router = useRouter()

  // A server page's error comes from its data: read again, or reset() shows the same failure.
  function retry() {
    startTransition(() => {
      router.refresh()
      reset()
    })
  }

  useEffect(() => {
    Sentry.captureException(error)
  }, [error])

  return (
    <main
      data-testid="error-page"
      className="mx-auto flex w-full max-w-page flex-1 flex-col items-center justify-center px-6 py-12"
    >
      <div className="w-full space-y-8 text-center">
        <div className="space-y-4">
          <h1 className="font-heading text-4xl font-medium tracking-tight text-balance sm:text-5xl">
            {t("title")}
          </h1>
          <p className="text-base text-muted-foreground">{t("text")}</p>
        </div>
        {/* Report beside the two; on phones on its own line under them. */}
        <div className="flex flex-wrap justify-center gap-3">
          <Button className="h-12 px-6 text-base" onClick={retry}>
            {common("retry")}
          </Button>
          <Button
            variant="outline"
            className="h-12 px-6 text-base"
            render={<Link href="/" />}
            nativeButton={false}
          >
            {common("home")}
          </Button>
          <div className="flex justify-center max-sm:basis-full">
            <ReportProblem />
          </div>
        </div>
      </div>
    </main>
  )
}
