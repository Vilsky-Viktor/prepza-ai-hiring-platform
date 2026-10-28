"use client"

import { useLocalTime } from "@/hooks/use-local-time"

/** A moment as its date (and time, with `withTime`) in the visitor's own time zone, for pages
 * rendered on the server. */
export function LocalDate({
  iso,
  withTime = false,
}: {
  iso: string
  withTime?: boolean
}) {
  const { date, dateTime } = useLocalTime()

  return <time dateTime={iso}>{withTime ? dateTime(iso) : date(iso)}</time>
}
